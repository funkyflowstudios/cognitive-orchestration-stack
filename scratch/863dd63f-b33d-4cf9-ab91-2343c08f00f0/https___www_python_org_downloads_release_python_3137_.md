Notice: While JavaScript is not essential for this website, your interaction with the content will be limited. Please turn JavaScript on for the full experience.

python™

Donate

≡ Menu

A A

Smaller

Larger

Reset

Socialize

LinkedIn

Mastodon

Chat on IRC

Twitter

Python 3.13.7

Release Date: Aug. 14, 2025

This is the seventh maintenance release of Python 3.13

Python 3.13 is the newest major release of the Python programming language, and it contains many new features and optimizations compared to Python 3.12. 3.13.7 is the seventh maintenance release of 3.13.

3.13.7 is an expedited release to fix a significant issue with the 3.13.6 release:

gh-137583: Regression in ssl module between 3.13.5 and 3.13.6: reading from a TLS-encrypted connection blocks

A few other bug fixes (which would otherwise have waited until the next release) are also included.

Major new features of the 3.13 series, compared to 3.12

Some of the new major new features and changes in Python 3.13 are:

New features

A new and improved interactive interpreter, based on PyPy's, featuring multi-line editing and color support, as well as colorized exception tracebacks.

An experimental free-threaded build mode, which disables the Global Interpreter Lock, allowing threads to run more concurrently. The build mode is available as an experimental feature in the Windows and macOS installers as well.

A preliminary, experimental JIT, providing the ground work for significant performance improvements.

The locals() builtin function (and its C equivalent) now has well-defined semantics when mutating the returned mapping, which allows debuggers to operate more consistently.

A modified version of mimalloc is now included, optional but enabled by default if supported by the platform, and required for the free-threaded build mode.

Docstrings now have their leading indentation stripped, reducing memory use and the size of .pyc files. (Most tools handling docstrings already strip leading indentation.)

The dbm module has a new dbm.sqlite3 backend that is used by default when creating new files.

The minimum supported macOS version was changed from 10.9 to 10.13 (High Sierra). Older macOS versions will not be supported going forward.

WASI is now a Tier 2 supported platform. Emscripten is no longer an officially supported platform (but Pyodide continues to support Emscripten).

iOS is now a Tier 3 supported platform.

Android is now a Tier 3 supported platform.

Typing

Support for type defaults in type parameters.

A new type narrowing annotation, typing.TypeIs.

A new annotation for read-only items in TypeDicts.

A new annotation for marking deprecations in the type system.

Removals and new deprecations

PEP 594 (Removing dead batteries from the standard library) scheduled removals of many deprecated modules: aifc, audioop, chunk, cgi, cgitb, crypt, imghdr, mailcap, msilib, nis, nntplib, ossaudiodev, pipes, sndhdr, spwd, sunau, telnetlib, uu, xdrlib, lib2to3.

Many other removals of deprecated classes, functions and methods in various standard library modules.

C API removals and deprecations. (Some removals present in alpha 1 were reverted in alpha 2, as the removals were deemed too disruptive at this time.)

New deprecations, most of which are scheduled for removal from Python 3.15 or 3.16.

For more details on the changes to Python 3.13, see What's new in Python 3.13.

More resources

Online Documentation

PEP 719, 3.13 Release Schedule

Report bugs at https://github.com/python/cpython/issues.

Help fund Python directly (or via GitHub Sponsors), and support the Python community.

Full Changelog

Files

Version Operating System Description MD5 Sum File Size GPG Sigstore SBOM Gzipped source tarball Source release 138c2e19c835ead10499571e0d4cf189 28.0 MB SIG .sigstore SPDX XZ compressed source tarball Source release 256cdb3bbf45cdce7499e52ba6c36ea3 21.7 MB SIG .sigstore SPDX macOS 64-bit universal2 installer macOS for macOS 10.13 and later ac0421b04eef155f4daab0b023cf3956 67.8 MB SIG .sigstore Windows installer (64-bit) Windows Recommended 1da92e43c79f3d1539dd23a3c14bf3f0 27.5 MB SIG .sigstore SPDX Windows installer (32-bit) Windows f501c1b321c82412ed330ec5604cac39 26.2 MB SIG .sigstore SPDX Windows installer (ARM64) Windows Experimental 66c0ba98b20b7d4ea0904223d484d369 26.8 MB SIG .sigstore SPDX Windows embeddable package (64-bit) Windows 77f294ec267596827a2ab06e8fa3f18c 10.4 MB SIG .sigstore SPDX Windows embeddable package (32-bit) Windows 53eaef0de1231fdf133ea703e3e43b30 9.2 MB SIG .sigstore SPDX Windows embeddable package (ARM64) Windows 6a3fcfc7a10a3822459b1c214f769df1 9.7 MB SIG .sigstore SPDX Windows release manifest Windows Install with 'py install 3.13' 6a5588452e73f959c9fa1ba009f42f75 14.6 KB .sigstore

▲ Back to Top

About

Applications

Quotes

Getting Started

Help

Python Brochure

Downloads

All releases

Source code

Windows

macOS

Android

Other Platforms

License

Alternative Implementations

Documentation

Docs

Audio/Visual Talks

Beginner's Guide

Developer's Guide

FAQ

Non-English Docs

PEP Index

Python Books

Python Essays

Community

Diversity

Mailing Lists

IRC

Forums

PSF Annual Impact Report

Python Conferences

Special Interest Groups

Python Logo

Python Wiki

Code of Conduct

Community Awards

Get Involved

Shared Stories

Success Stories

Arts

Business

Education

Engineering

Government

Scientific

Software Development

News

Python News

PSF Newsletter

PSF News

PyCon US News

News from the Community

Events

Python Events

User Group Events

Python Events Archive

User Group Events Archive

Submit an Event

Contributing

Developer's Guide

Issue Tracker

python-dev list

Core Mentorship

Report a Security Issue

▲ Back to Top

Help & General Contact

Diversity Initiatives

Submit Website Bug

Status

Copyright ©2001-2025. Python Software Foundation Legal Statements Privacy Notice