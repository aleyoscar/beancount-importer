
<a name="v0.1.1"></a>
## [v0.1.1](https://github.com/aleyoscar/beancount-importer/compare/v0.1.0...v0.1.1) (2025-08-27)

### Bug Fixes

* **app:** Insert txn if matches not desired. Fixes [#1](https://github.com/aleyoscar/beancount-importer/issues/1)
* **app:** Remove autocomplete duplicates. Fixes [#2](https://github.com/aleyoscar/beancount-importer/issues/2)

### Code Refactoring

* **app:** Cleanup code

### Features

* **app:** Allow cancelling during insertion. Closes [#3](https://github.com/aleyoscar/beancount-importer/issues/3)


<a name="v0.1.0"></a>
## v0.1.0 (2025-08-26)

### Bug Fixes

* **app:** UTF-8 encoding
* **app:** Fix rec insertion
* **app:** Remove old account/id entry reconciliation method
* **app:** Only replace payee if inserting
* **app:** Update ledger info for every ofx transaction
* **app:** Write all files with LF line endings
* **app:** Insert newlines between transactions in buffer
* **app:** Typo in edit tags
* **app:** Performing regex fullmatch for validators
* **app:** Debit not negative
* **app:** Compare bean and ofx with absolute values
* **app:** Remove duplicate spaces
* **app:** Bad date reference
* **app:** Fix append to file
* **app:** Removed duplicate replace_payee calls

### Code Refactoring

* **app:** Reconcile based on postings
* **app:** Moved final log after buffer
* **app:** Consolidate validator options
* **app:** Replaced ofx data with account class
* **app:** Check resolve choice with first letter
* **app:** Moved theme into main

### Features

* **app:** Add counter
* **app:** Check postings for match when reconciling
* **app:** Add cli option shorthands. Add skip currency prompt
* **app:** Add completion for tags and links
* **app:** Edit transaction postings
* **app:** Edit transaction links
* **app:** Edit transaction tags
* **app:** Edit transaction narration
* **app:** Added final counts
* **app:** Edit transaction payee
* **app:** Edit transaction flag
* **app:** Edit transaction date
* **app:** Skeleton edit transaction
* **app:** Insert ofx information into beancount transaction
* **app:** Autocomplete beancount accounts
* **app:** Import transactions
* **app:** Reconcile transactions
* **app:** Iterate through pending txns and replace payee
* **app:** Add checks for empty lists
* **app:** Find pending transactions not in ledger
* **app:** Filter transactions by date
* **app:** Parse beancount ledger file
* **app:** Added currency print helper
* **app:** Parse ofx transactions
* **app:** Added promptsession and skeleton structure
* **app:** Validate ofx and ledger file paths
* **app:** Add prompt_toolkit dependency
* **core:** Add GNU GPL-3.0 license

