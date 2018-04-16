// Copyright (c) 2018-present, Facebook, Inc.
// All Rights Reserved.
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.

// Definitions for interfacing with SQL data stores using the diesel library.

use std::io::Write;

use diesel::backend::Backend;
use diesel::deserialize::{self, FromSql};
use diesel::serialize::{self, IsNull, Output, ToSql};
use diesel::sql_types::Binary;

use errors::*;
use nodehash::{HgChangesetId, HgManifestId, HgNodeHash};

#[derive(QueryId, SqlType)]
#[mysql_type = "Blob"]
#[sqlite_type = "Binary"]
pub struct HgChangesetIdSql;

#[derive(QueryId, SqlType)]
#[mysql_type = "Blob"]
#[sqlite_type = "Binary"]
pub struct HgManifestIdSql;

impl<DB: Backend> ToSql<HgChangesetIdSql, DB> for HgChangesetId {
    fn to_sql<W: Write>(&self, out: &mut Output<W, DB>) -> serialize::Result {
        out.write_all(self.as_nodehash().as_ref())?;
        Ok(IsNull::No)
    }
}

impl<DB: Backend> FromSql<HgChangesetIdSql, DB> for HgChangesetId
where
    *const [u8]: FromSql<Binary, DB>,
{
    fn from_sql(bytes: Option<&DB::RawValue>) -> deserialize::Result<Self> {
        // Using unsafe here saves on a heap allocation. See https://goo.gl/K6hapb.
        let raw_bytes: *const [u8] = FromSql::<Binary, DB>::from_sql(bytes)?;
        let raw_bytes: &[u8] = unsafe { &*raw_bytes };
        let hash = HgNodeHash::from_bytes(raw_bytes).compat()?;
        Ok(Self::new(hash))
    }
}

impl<DB: Backend> ToSql<HgManifestIdSql, DB> for HgManifestId {
    fn to_sql<W: Write>(&self, out: &mut Output<W, DB>) -> serialize::Result {
        out.write_all(self.as_nodehash().as_ref())?;
        Ok(IsNull::No)
    }
}

impl<DB: Backend> FromSql<HgManifestIdSql, DB> for HgManifestId
where
    *const [u8]: FromSql<Binary, DB>,
{
    fn from_sql(bytes: Option<&DB::RawValue>) -> deserialize::Result<Self> {
        // Using unsafe here saves on a heap allocation. See https://goo.gl/K6hapb.
        let raw_bytes: *const [u8] = FromSql::<Binary, DB>::from_sql(bytes)?;
        let raw_bytes: &[u8] = unsafe { &*raw_bytes };
        let hash = HgNodeHash::from_bytes(raw_bytes).compat()?;
        Ok(Self::new(hash))
    }
}
