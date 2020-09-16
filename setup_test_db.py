import sqlalchemy # type: ignore
import lighthouse.config.test as config # type: ignore

# Set up a basic MLWH db for testing
"""Drop and recreate required tables."""
print("Initialising the test MySQL warehouse database")

create_engine_string = f"mysql+pymysql://{config.MLWH_CONN_STRING}/{config.ML_WH_DB}"
sql_engine = sqlalchemy.create_engine(create_engine_string, pool_recycle=3600)

create_db = """
CREATE DATABASE IF NOT EXISTS `unified_warehouse_test` /*!40100 DEFAULT CHARACTER SET latin1 */;
"""
drop_table = """
DROP TABLE IF EXISTS `unified_warehouse_test`.`lighthouse_sample`;
"""
create_table = """
CREATE TABLE `unified_warehouse_test`.`lighthouse_sample` (
`id` int NOT NULL AUTO_INCREMENT,
`mongodb_id` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Auto-generated id from MongoDB',
`root_sample_id` varchar(255) COLLATE utf8_unicode_ci NOT NULL COMMENT 'Id for this sample provided by the Lighthouse lab',
`cog_uk_id` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Consortium-wide id, generated by Sanger on import to LIMS',
`rna_id` varchar(255) COLLATE utf8_unicode_ci NOT NULL COMMENT 'Lighthouse lab-provided id made up of plate barcode and well',
`plate_barcode` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Barcode of plate sample arrived in, from rna_id',
`coordinate` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Well position from plate sample arrived in, from rna_id',
`result` varchar(255) COLLATE utf8_unicode_ci NOT NULL COMMENT 'Covid-19 test result from the Lighthouse lab',
`date_tested_string` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'When the covid-19 test was carried out by the Lighthouse lab',
`date_tested` datetime DEFAULT NULL COMMENT 'date_tested_string in date format',
`source` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Lighthouse centre that the sample came from',
`lab_id` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'Id of the lab, within the Lighthouse centre',
`created_at_external` datetime DEFAULT NULL COMMENT 'When the corresponding record was inserted into the MongoDB',
`updated_at_external` datetime DEFAULT NULL COMMENT 'When the corresponding record was last updated in MongoDB',
`created_at` datetime DEFAULT NULL COMMENT 'When this record was inserted',
`updated_at` datetime DEFAULT NULL COMMENT 'When this record was last updated',
PRIMARY KEY (`id`),
UNIQUE KEY `index_lighthouse_sample_on_root_sample_id_and_rna_id_and_result` (`root_sample_id`,`rna_id`,`result`),
UNIQUE KEY `index_lighthouse_sample_on_mongodb_id` (`mongodb_id`),
KEY `index_lighthouse_sample_on_date_tested` (`date_tested`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
"""

with sql_engine.connect() as connection:
  connection.execute(create_db)
  connection.execute(drop_table)
  connection.execute(create_table)

print("Done")