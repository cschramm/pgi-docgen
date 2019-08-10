# Copyright 2016 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import json

from ..debian import get_repo_typelibs
from ..girdata import get_debian_path


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "update-debian-info", help="Update the debian package information")
    parser.set_defaults(func=main)


def main(args):
    import apt

    cache = apt.Cache()
    cache.open(None)

    typelibs = get_repo_typelibs()

    def fixup_desc(t):
        new = []
        for line in t.splitlines():
            if line.startswith(
                    ("This package includes", "This package contains",
                     "This package provides")):
                continue
            new.append(line)
        return "\n".join(new).strip()

    def fixup_summary(t):
        return t.rsplit(" - ", 1)[0].rsplit(" -- ", 1)[0]

    final = {}
    for package, namespaces in typelibs.items():
        candidate = cache[package].candidate
        if not candidate:
            continue

        # For a package containing the typelib search for a direct dependency
        # which is a library and has the same source package.
        # This library package usually has a better description/summary.
        dep_packages = []
        for deps in candidate.get_dependencies("Depends"):
            for dep in deps:
                if dep.name in cache:
                    cand = cache[dep.name].candidate
                    if cand:
                        dep_packages.append(cand)

        for dep in dep_packages:
            if dep.section != "libs":
                continue
            if dep.source_name == candidate.source_name:
                candidate = dep
                break

        def extract_version(version):
            version = version.split(":", 1)[-1]
            for s in "-~+":
                version = version.rsplit(s, 1)[0]
            return version

        homepage = candidate.homepage
        summary = fixup_summary(candidate.summary)
        description = fixup_desc(candidate.description)
        version = extract_version(candidate.source_version)

        for ns in namespaces:
            final[ns] = {
                "lib": candidate.source_name,
                "homepage": homepage,
                "summary": summary,
                "description": description,
                "debian_package": package,
                "version": version,
            }

    cache.close()

    with open(get_debian_path(), "wb") as h:
        h.write(json.dumps(final, sort_keys=True, indent=4).encode("utf-8"))
