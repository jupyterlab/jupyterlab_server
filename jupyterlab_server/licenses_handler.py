"""Tornado handlers for license reporting."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import mimetypes
import json
import re
import csv
import io
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor

from tornado import web, gen

from traitlets import Unicode, List
from traitlets.config import LoggingConfigurable

from .server import APIHandler
from .config import get_federated_extensions


class LicensesManager(LoggingConfigurable):
    """A manager for listing the licenses for all frontend end code distributed
    by an application and any federated extensions
    """

    executor = ThreadPoolExecutor(max_workers=1)

    third_party_licenses_files = List(
        Unicode(),
        default_value=["third-party-licenses.json"],
        help="the license report data in built app and federated extensions",
    )

    @property
    def federated_extensions(self):
        """Lazily load the currrently-available federated extensions.

        This is expensive, but probably the only way to be sure to get
        up-to-date interactively-installed extensions.
        """
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
            return (
                self.report_markdown(licenses, full_text=full_text),
                "text/markdown",
            )

    def report_csv(self, licenses):
        """create a CSV report"""
        outfile = io.StringIO()
        fieldnames = ["name", "versionInfo", "licenseId", "extractedText"]
        writer = csv.DictWriter(outfile, fieldnames=["bundle"] + fieldnames)
        writer.writeheader()
        for bundle_name, bundle in licenses.items():
            for package in bundle["packages"]:
                writer.writerow(
                    {
                        "bundle": bundle_name,
                        **{field: package.get(field, "") for field in fieldnames},
                    }
                )
        return outfile.getvalue()

    def report_markdown(self, licenses, full_text=True):
        """create a markdown report"""
        lines = []
        library_names = [
            len(package["name"])
            for bundle_name, bundle in licenses.items()
            for package in bundle.get("packages", [])
        ]
        longest_name = max(library_names) if library_names else 1

        for bundle_name, bundle in licenses.items():
            # TODO: parametrize template
            lines += [f"# {bundle_name}", ""]

            packages = bundle.get("packages", [])
            if not packages:
                lines += ["> No licenses found", ""]
                continue

            for package in packages:
                lines += [
                    "## "
                    + (
                        "\t".join(
                            [
                                f"""**{package["name"].strip()}**""".ljust(
                                    longest_name
                                ),
                                f"""`{package["versionInfo"] or ""}`""".ljust(20),
                                (package["licenseId"] or ""),
                            ]
                        )
                    )
                ]
                if full_text:
                    text = package["extractedText"]
                    if not text.strip():
                        lines += ["", "> No license text available", ""]
                    else:
                        lines += ["", "", "```", text, "```", ""]
        return "\n".join(lines)

    def license_bundle(self, path, bundle):
        """Return the content of a packages's license bundles"""
        bundle_json = {"packages": []}

        for license_file in self.third_party_licenses_files:
            licenses_path = path / license_file
            if not licenses_path.exists():
                self.log.warn(
                    "Third-party licenses not found for %s: %s", bundle, licenses_path
                )
                continue

            try:
                file_text = licenses_path.read_text(encoding="utf-8")
            except Exception as err:
                self.log.warn(
                    "Failed to open third-party licenses for %s: %s\n%s",
                    bundle,
                    licenses_path,
                    err,
                )
                continue

            try:
                file_json = json.loads(file_text)
            except Exception as err:
                self.log.warn(
                    "Failed to parse third-party licenses for %s: %s\n%s",
                    bundle,
                    licenses_path,
                    err,
                )
                continue

            try:
                bundle_json["packages"].extend(file_json["packages"])
            except Exception as err:
                self.log.warn(
                    "Failed to find packages for %s: %s\n%s",
                    bundle,
                    licenses_path,
                    err,
                )
                continue

        return bundle_json

    def app_static_info(self):
        """get the static directory for this app"""
        path = Path(self.parent.app_dir) / "static"
        package_json = path / "package.json"
        if self.parent.dev_mode:
            package_json = path.parent / "package.json"
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
            licenses[ext_name] = self.license_bundle(
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
        download = bool(json.loads(self.get_argument("download", "0")))
        if download:
            filename = "{}-licenses{}".format(
                self.manager.parent.app_name.lower(), mimetypes.guess_extension(mime)
            )
            self.set_attachment_header(filename)
        self.write(report)
        self.set_header("Content-Type", mime)
