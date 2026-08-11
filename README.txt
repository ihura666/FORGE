FORGE v1.0.0
============

FORGE is a controlled wordlist generation application.

It provides several generation modes, configurable candidate limits,
duplicate prevention, project state saving, continuation, and multiple
traversal strategies.

QUICK START
-----------

Run:

    ./FORGE

The main menu contains:

    passwords
    continue
    emails
    user_manual
    exhaustive
    quit

If you do not understand an option, choose:

    user_manual

PASSWORDS
---------

Generates password candidates from keywords, numbers, symbols and
configured generation rules.

EMAILS
------

Generates email candidates from supplied keywords, numbers, symbols,
and domains.

EXHAUSTIVE
----------

Generates candidates across a defined alphabet and length range.

Available traversal strategies:

    1. Sequential
    2. Priority
    3. Rotation
    4. Alphabetical
    5. Random

CONTINUE
--------

Resumes a previously saved FORGE project.

USER MANUAL
-----------

The user_manual option provides detailed explanations and examples
for the program's features and terminology.

CANDIDATE LIMITS
----------------

FORGE allows the user to specify the maximum number of NEW candidates
to generate during an operation.

This is important because candidate spaces can become extremely large.

For an alphabet containing N characters and a fixed length L, the basic
exhaustive space is:

    N^L

For example:

    4 characters
    length 8

produces:

    4^8 = 65,536

possible strings.

Always use reasonable limits when testing.

DUPLICATE PREVENTION
--------------------

FORGE tracks generated candidates and can compare new candidates with
existing wordlists to prevent unnecessary duplication.

PROJECT STATE
-------------

FORGE saves project information needed to continue interrupted
generation.

RELEASE
-------

Version: 1.0.0
Status: Initial stable release

COPYRIGHT
---------

Copyright © 2026 Lord Ihura.
All rights reserved.

See LICENSE.txt and COPYRIGHT.txt.

For detailed instructions, use USER_MANUAL.txt or select user_manual
inside FORGE.
