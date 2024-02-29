0001 Purpose of This Repo
#########################

Status
******

**Accepted**

Context
*******

This repository holds Aspects-related plugins for the Open edX LMS and Studio. It will likely supersede some other repositories such as openedx-event-sink-clickhouse and gather them into a single repository for maintainability.

Decision
********

We will create a repository to hold all LMS / Studio plugins in one place, with settings or feature flags to enable the different specific features.

Consequences
************

* This repository is created.

Rejected Alternatives
*********************

Currently licensing issues prevent us from combining this with openedx-aspects, however we may choose to do that in the future.

.. _Documenting Architecture Decisions: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
.. _OEP-19 on ADRs: https://open-edx-proposals.readthedocs.io/en/latest/best-practices/oep-0019-bp-developer-documentation.html#adrs
