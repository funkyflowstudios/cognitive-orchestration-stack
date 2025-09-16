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

Python 3.12.0

Release Date: Oct. 2, 2023

This is the stable release of Python 3.12.0

Python 3.12.0 is the newest major release of the Python programming language, and it contains many new features and optimizations.

Major new features of the 3.12 series, compared to 3.11

New features

More flexible f-string parsing, allowing many things previously disallowed (PEP 701).

Support for the buffer protocol in Python code (PEP 688).

A new debugging/profiling API (PEP 669).

Support for isolated subinterpreters with separate Global Interpreter Locks (PEP 684).

Even more improved error messages. More exceptions potentially caused by typos now make suggestions to the user.

Support for the Linux perf profiler to report Python function names in traces.

Many large and small performance improvements (like PEP 709 and support for the BOLT binary optimizer), delivering an estimated 5% overall performance improvement.

Type annotations

New type annotation syntax for generic classes (PEP 695).

New override decorator for methods (PEP 698).

Deprecations

The deprecated wstr and wstr_length members of the C implementation of unicode objects were removed, per PEP 623.

In the unittest module, a number of long deprecated methods and classes were removed. (They had been deprecated since Python 3.1 or 3.2).

The deprecated smtpd and distutils modules have been removed (see PEP 594 and PEP 632. The setuptools package continues to provide the distutils module.

A number of other old, broken and deprecated functions, classes and methods have been removed.

Invalid backslash escape sequences in strings now warn with SyntaxWarning instead of DeprecationWarning, making them more visible. (They will become syntax errors in the future.)

The internal representation of integers has changed in preparation for performance enhancements. (This should not affect most users as it is an internal detail, but it may cause problems for Cython-generated code.)

For more details on the changes to Python 3.12, see What's new in Python 3.12.

More resources

Online Documentation.

PEP 693, the Python 3.12 Release Schedule.

Report bugs via GitHub Issues.

Help fund Python and its community.

And now for something completely different

They have no need of our help
So do not tell me
These haggard faces could belong to you or me
Should life have dealt a different hand
We need to see them for who they really are
Chancers and scroungers
Layabouts and loungers
With bombs up their sleeves
Cut-throats and thieves
They are not
Welcome here
We should make them
Go back to where they came from
They cannot
Share our food
Share our homes
Share our countries
Instead let us
Build a wall to keep them out
It is not okay to say
These are people just like us
A place should only belong to those who are born there
Do not be so stupid to think that
The world can be looked at another way

(now read from bottom to top)

Refugees, by Brian Bilston.

Full Changelog

Files

Version Operating System Description MD5 Sum File Size GPG Sigstore Gzipped source tarball Source release d6eda3e1399cef5dfde7c4f319b0596c 25.9 MB SIG .sigstore XZ compressed source tarball Source release f6f4616584b23254d165f4db90c247d6 19.6 MB SIG .sigstore macOS 64-bit universal2 installer macOS for macOS 10.9 and later eddf6f35a3cbab94f2f83b2875c5fc27 43.3 MB SIG .sigstore Windows installer (64-bit) Windows Recommended 32ab6a1058dfbde76951b7aa7c2335a6 25.3 MB SIG .sigstore Windows installer (32-bit) Windows de59862985bf7afa639f2e4f9e2a722c 24.0 MB SIG .sigstore Windows installer (ARM64) Windows Experimental 230c703e3b8b3d92765d118afa7b2f78 24.5 MB SIG .sigstore Windows embeddable package (64-bit) Windows 8e24d2b26a8dbf1da0694b9da1a08b2c 10.5 MB SIG .sigstore Windows embeddable package (32-bit) Windows c2047dc270c4936f9c64619bb193b721 9.4 MB SIG .sigstore Windows embeddable package (ARM64) Windows 3da91ef1a86a8a210a32ea99c709dd93 9.8 MB SIG .sigstore

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