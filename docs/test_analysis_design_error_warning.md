# Dataset health semantics

`ERROR` blocks Test Analysis & Design proposal generation because the governed source cannot be trusted structurally. Examples: broken schema, missing required field, broken reference, duplicate ID, corrupted record.

`WARNING` is surfaced but does not automatically block. Examples: inactive related record, high similarity, coverage overlap, consolidation opportunity. The reviewer decides whether to add, extend, edit, reject, or skip.
