Change Log
##########

..
   All enhancements and patches to platform_plugin_aspects will be documented
   in this file.  It adheres to the structure of https://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (https://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
**********

0.11.2 - 2024-10-04
*******************

Fixes
=====

* wait for transaction commit before trying to sink models.

0.11.1 - 2024-09-06
*******************

Fixes
=====

* delay loading of unfocused dashboards in LMS.

0.11.0 - 2024-09-04
*******************

Added
=====

* A sink for the object tags, tags and taxonomy.

0.10.0 - 2024-06-17
*******************

Added
=====

* A sink for the course enrollment model.

0.9.7 - 2024-06-14
******************

Fixes
=====

* 0.9.6 introduced a bug in the CourseOverview sink that caused block sink to fail to import to ClickHouse, this fixes it.


0.9.6 - 2024-06-07
******************

Fixes
=====

* The CourseOutline sink was not always ordering blocks correctly, leading to issues with blocks appearing in the wrong sections/subsection.


0.9.5 - 2024-05-24
******************

Fixes
=====

* UserProfile sink now runs after the transaction is committed, preventing UserProfileNotFound errors and creation of rows in ClickHouse that don't exist in MySQL in the case of a rollback.


0.9.4 - 2024-05-16
******************

Fixes
=====

* Allow to serialize dates as strings in JSON.

0.9.3 - 2024-05-15
******************

Fixes
=====

* Change wording of the "go to Superset" link, and make it optional.


0.9.2 - 2024-05-08
******************

Fixes
=====

* Remove caching of Superset guest token to fix various display errors and token refresh edge cases.

0.9.1 - 2024-05-08
******************

Fixes
=====

* Fix an ImportError in the Aspects Xblock on pre-Quince releases


0.9.0 - 2024-05-06
******************

Added
=====

* Allow embedded dashboard tab names to be localized

0.8.0 - 2024-05-06
******************

Added
=====

* Added tags to xblocks in course dump


0.7.4 - 2024-04-30
******************

Fixed
=====
* Fixed Superset XBlock and default filters.

0.7.3 - 2024-04-30
******************

Fixed
=====

* Fixed UUID generation for localized Superset assets, which caused embedded
  dashboards to fail to load when localized.

0.7.2 - 2024-04-19
******************

Fixed
=====

* Fixed cms url configuration

0.7.1 - 2024-04-17
******************

Fixed
=====

* Fixed issue with embedded dashboards throwing javascript errors
* Fixed issues with translated embedded dashboards erroring in Superset

0.7.0 - 2024-04-12
******************

Added
=====

* Add endpoint for fetchGuestToken

0.6.0 - 2024-04-08
******************

Added
=====

* Allow to embed translated Superset Dashboards.

0.5.0 - 2024-04-01
******************

Added
=====

* Load testing and test monitoring scripts.

0.4.0 - 2024-03-18
******************

Added
=====

* Embed multiple Superset Dashboards.

0.3.1 - 2024-03-14
******************

Added
=====

* Fixed development server configuration.

0.3.0 – 2024-03-10
******************

Added
=====

* Imported XBlock code from platform-plugin-superset

0.2.0 – 2024-03-05
******************

Added
=====

* Imported code from event-sink-clickhouse.

0.1.0 – 2024-02-29
**********************************************

Added
=====

* First release on PyPI.
