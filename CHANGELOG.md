# Change Log
## [Unreleased]
### Added
- Ability to get the user account that an instantiated `ShinobiMonitorOrm` uses.
- Missing imports to root `__init__.py` module.

### Removed
- Configuration duplication in improved monitor data.
- `ok` from returned data.

## 2.0.1
### Added
- Improved fields in monitor data.
- GPLv3 licence.

## 2.0.0
### Changed
- A super user token is no longer required to instantiate a `ShinobiClient`. A
  `ShinobiSuperUserCredentialsRequiredError` will be raised at the point at which it is needed if it has not been
  supplied.
- Details about a user can be queried without a super user token.
- A user's API key can be attained without a super user token.
- More specialised errors.
- Change to name of verify flags on User ORM's create and delete methods to unify them.
- Method to modify user now returns whether a modification occurs, without requiring a modified Shinobi installation.

### Added
- Monitor ORM.

## 1.0.0
Initial release.
