"""Tornado handlers for license reporting."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import re
import csv
import textwrap
import io
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor

from tornado.platform.asyncio import to_tornado_future
from tornado import web, gen

from traitlets import default, Dict, Unicode, Instance
from traitlets.config import LoggingConfigurable

from .server import APIHandler
from .config import get_federated_extensions, LabConfig


class LicensesManager(LoggingConfigurable):
    """A manager for listing the licenses for all frontend end code distributed
    by an application and any federated extensions
    """

    executor = ThreadPoolExecutor(max_workers=1)

    federated_extensions = Dict()

    third_party_licenses_file = Unicode(
        "third-party-licenses.json",
        help="the license report data in built app and federated extensions",
    )

    @default("federated_extensions")
    def _default_federated_extensions(self):
        """Lazily load the app info. This is expensive, but probably the only
        way to be sure.
        """
        # TODO: this is expensive, probably calculated already for parent
        labextensions_path = sum(
            [
                self.parent.labextensions_path,
                self.parent.extra_labextensions_path,
            ],
            [],
        )
        return get_federated_extensions(labextensions_path)

    @gen.coroutine
    def report_async(
        self, report_format="markdown", bundles_pattern=".*", full_text=False
    ):
        """Asynchronous wrapper around the potentially slow job of locating
        and encoding all of the licenses
        """
        report = yield self.executor.submit(
            self.report,
            report_format=report_format,
            bundles_pattern=bundles_pattern,
            full_text=full_text,
        )
        return report

    def report(self, report_format, bundles_pattern, full_text):
        """create a human- or machine-readable report"""
        licenses = self.licenses(bundles_pattern=bundles_pattern)
        if report_format == "json":
            return json.dumps(licenses, indent=2, sort_keys=True), "application/json"
        elif report_format == "csv":
            return self.report_csv(licenses), "text/csv"
        elif report_format == "markdown":
            return (self.report_markdown(licenses, full_text=full_text), "text/plain")

    def report_csv(self, licenses):
        """create a CSV report"""
        outfile = io.StringIO()
        writer = csv.DictWriter(
            outfile,
            fieldnames=["bundle", "library", "version", "licenseId", "licenseText"],
        )
        writer.writeheader()
        for bundle_name, bundle in licenses.items():
            if not bundle or "licenses" not in bundle:
                continue
            for library, spec in bundle.get("licenses", {}).items():
                writer.writerow({"bundle": bundle_name, "library": library, **spec})
        return outfile.getvalue()

    def report_markdown(self, licenses, full_text=True):
        """create a markdown report"""
        lines = []
        library_names = [
            len(library_name)
            for bundle_name, bundle in licenses.items()
            if bundle and "licenses" in bundle
            for library_name in bundle["licenses"]
        ]
        longest_name = max(library_names) if library_names else 1
        for bundle_name, bundle in licenses.items():
            # TODO: parametrize template
            lines += [f"# {bundle_name}", ""]

            if bundle is None or "licenses" not in bundle:
                lines += ["> No licenses found", ""]
                continue

            for library, spec in bundle.get("licenses", {}).items():
                lines += [
                    "- "
                    + (
                        "\t".join(
                            [
                                f"**{library.strip()}**".ljust(longest_name),
                                f"""`{spec["version"] or ""}`""".ljust(20),
                                (spec["licenseId"] or ""),
                            ]
                        )
                    )
                ]
                if full_text:
                    lines += [""]
                    if spec["licenseText"]:
                        lines += [
                            textwrap.indent(spec["licenseText"], " " * 6),
                            "",
                        ]
        return "\n".join(lines)

    def license_bundle(self, path, bundle):
        """Return the content of a path's license bundle, or None if it doesn't exist"""
        licenses_path = path / self.third_party_licenses_file
        if not licenses_path.exists():
            self.log.warn(
                "Third-party licenses not found for %s: %s", bundle, licenses_path
            )
            return None

        try:
            bundle_text = licenses_path.read_text(encoding="utf-8")
        except Exception as err:
            self.log.warn(
                "Failed to open third-party licenses for %s: %s\n%s",
                bundle,
                licenses_path,
                err,
            )
            return None

        try:
            bundle_json = json.loads(bundle_text)
        except Exception as err:
            self.log.warn(
                "Failed to parse third-party licenses for %s: %s\n%s",
                bundle,
                licenses_path,
                err,
            )
            return None

        return bundle_json

    def app_static_info(self):
        """get the static directory for this app"""
        path = Path(self.parent.app_dir) / "static"
        package_json = path / "package.json"
        if self.parent.dev_mode:
            path = path.parent / "package.json"
        name = json.loads(package_json.read_text(encoding="utf-8"))["name"]
        return path, name

    def licenses(self, bundles_pattern=".*") -> dict:
        """Read all of the licenses
        TODO: schema
        """
        licenses = {}

        app_path, app_name = self.app_static_info()
        if re.match(bundles_pattern, app_name):
            licenses[app_name] = self.license_bundle(app_path, app_name)

        for ext_name, ext_info in self.federated_extensions.items():
            if not re.match(bundles_pattern, ext_name):
                continue
            licenses[fed_ext] = self.license_bundle(
                Path(ext_info["ext_path"]), ext_name
            )

        return licenses


class LicensesHandler(APIHandler):
    """A handler for serving licenses used by the application"""

    def initialize(self, manager: LicensesManager):
        super(LicensesHandler, self).initialize()
        self.manager = manager

    @web.authenticated
    async def get(self, _args):
        """Return all the frontend licenses as JSON"""
        report, mime = await self.manager.report_async(
            report_format=self.get_argument("format", "json"),
            bundles_pattern=self.get_argument("bundles", ".*"),
            full_text=bool(json.loads(self.get_argument("full_text", "true"))),
        )
        self.write(report)
        self.set_header("Content-Type", mime)
