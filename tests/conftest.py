import copy
import json
import os
from http import HTTPStatus

import pytest
import responses
from lighthouse import create_app
from lighthouse.constants import PLATE_EVENT_SOURCE_ALL_NEGATIVES, PLATE_EVENT_SOURCE_COMPLETED
from lighthouse.helpers.dart_db import create_dart_connection, load_sql_server_script
from lighthouse.helpers.mysql_db import create_mysql_connection_engine, get_table
from lighthouse.messages.message import Message

from .data.fixture_data import (
    CENTRES,
    COG_UK_IDS,
    DART_MONGO_MERGED_SAMPLES,
    EVENT_WH_DATA,
    LOTS_OF_SAMPLES,
    LOTS_OF_SAMPLES_DECLARATIONS_PAYLOAD,
    MLWH_LH_SAMPLES,
    MLWH_LH_SAMPLES_MULTIPLE,
    MLWH_SAMPLE_LIGHTHOUSE_SAMPLE,
    MLWH_SAMPLE_STOCK_RESOURCE,
    MULTIPLE_ERRORS_SAMPLES_DECLARATIONS,
    SAMPLES,
    SAMPLES_DECLARATIONS,
    SAMPLES_DIFFERENT_PLATES,
    SAMPLES_FOR_MLWH_UPDATE,
    SAMPLES_NO_DECLARATION,
    SAMPLES_WITH_LAB_ID,
    SAMPLES_WITH_UUIDS,
    SOURCE_PLATES,
)


@pytest.fixture
def app():
    # set the 'EVE_SETTINGS' env variable to easily switch to the testing environment when creating
    #   an app
    os.environ["EVE_SETTINGS"] = "test.py"

    app = create_app()

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def centres(app):
    with app.app_context():
        centres_collection = app.data.driver.db.centres
        _ = centres_collection.insert_many(CENTRES)

    #  yield a copy so that the test change it however it wants
    yield copy.deepcopy(CENTRES)

    # clear up after the fixture is used
    with app.app_context():
        centres_collection.delete_many({})


@pytest.fixture
def empty_data_when_finish(app):
    yield

    with app.app_context():
        mydb = app.data.driver.db
        mydb.samples.delete_many({})
        mydb.samples_declarations.delete_many({})
        mydb.centres.delete_many({})


@pytest.fixture
def samples_declarations(app):
    with app.app_context():
        samples_declarations_collections = app.data.driver.db.samples_declarations
        _ = samples_declarations_collections.insert_many(SAMPLES_DECLARATIONS)

    yield copy.deepcopy(SAMPLES_DECLARATIONS)

    # clear up after the fixture is used
    with app.app_context():
        samples_declarations_collections.delete_many({})


@pytest.fixture
def lots_of_samples_declarations_payload(app):
    yield copy.deepcopy(LOTS_OF_SAMPLES_DECLARATIONS_PAYLOAD)


@pytest.fixture
def multiple_errors_samples_declarations_payload(app):
    yield copy.deepcopy(MULTIPLE_ERRORS_SAMPLES_DECLARATIONS)


@pytest.fixture
def lots_of_samples(app):
    with app.app_context():
        samples_collections = app.data.driver.db.samples
        _ = samples_collections.insert_many(LOTS_OF_SAMPLES)

    yield copy.deepcopy(LOTS_OF_SAMPLES)

    # clear up after the fixture is used
    with app.app_context():
        samples_collections.delete_many({})


@pytest.fixture
def samples(app):
    with app.app_context():
        samples_collection = app.data.driver.db.samples
        _ = samples_collection.insert_many(SAMPLES)

    #  yield a copy of that the test change it however it wants
    yield copy.deepcopy(SAMPLES)

    # clear up after the fixture is used
    with app.app_context():
        samples_collection.delete_many({})


@pytest.fixture
def samples_different_plates(app):
    with app.app_context():
        samples_collection = app.data.driver.db.samples
        _ = samples_collection.insert_many(SAMPLES_DIFFERENT_PLATES)

    #  yield a copy of that the test change it however it wants
    yield copy.deepcopy(SAMPLES_DIFFERENT_PLATES)

    # clear up after the fixture is used
    with app.app_context():
        samples_collection.delete_many({})


@pytest.fixture
def samples_no_declaration(app):
    with app.app_context():
        samples_collection = app.data.driver.db.samples
        _ = samples_collection.insert_many(SAMPLES_NO_DECLARATION)

    #  yield a copy of that the test change it however it wants
    yield copy.deepcopy(SAMPLES_NO_DECLARATION)

    # clear up after the fixture is used
    with app.app_context():
        samples_collection.delete_many({})


@pytest.fixture
def source_plates(app):
    with app.app_context():
        source_plates_collection = app.data.driver.db.source_plates
        _ = source_plates_collection.insert_many(SOURCE_PLATES)

    #  yield a copy of that the test change it however it wants
    yield copy.deepcopy(SOURCE_PLATES)

    # clear up after the fixture is used
    with app.app_context():
        source_plates_collection.delete_many({})


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def labwhere_samples_simple(app, mocked_responses):
    labwhere_url = f"http://{app.config['LABWHERE_URL']}/api/labwares_by_barcode"

    body = json.dumps([{"barcode": "123", "location_barcode": "4567"}])
    mocked_responses.add(
        responses.POST,
        labwhere_url,
        body=body,
        status=HTTPStatus.OK,
    )


@pytest.fixture
def labwhere_samples_multiple(app, mocked_responses):
    labwhere_url = f"http://{app.config['LABWHERE_URL']}/api/labwares_by_barcode"

    body = json.dumps(
        [
            {"barcode": "123", "location_barcode": "4567"},
            {"barcode": "456", "location_barcode": "1234"},
            {"barcode": "789", "location_barcode": None},
        ]
    )
    mocked_responses.add(
        responses.POST,
        labwhere_url,
        body=body,
        status=HTTPStatus.OK,
    )


@pytest.fixture
def labwhere_samples_error(app, mocked_responses):
    labwhere_url = f"http://{app.config['LABWHERE_URL']}/api/labwares_by_barcode"

    body = json.dumps([])
    mocked_responses.add(
        responses.POST,
        labwhere_url,
        body=body,
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )


@pytest.fixture
def samples_for_mlwh_update(cog_uk_ids):
    return SAMPLES_FOR_MLWH_UPDATE


@pytest.fixture
def cog_uk_ids():
    return COG_UK_IDS


# ********************** WAREHOUSE DATA ************************** #


@pytest.fixture
def mlwh_lh_samples(app, mlwh_sql_engine):
    insert_into_mlwh(
        app, MLWH_LH_SAMPLES, mlwh_sql_engine, app.config["MLWH_LIGHTHOUSE_SAMPLE_TABLE"]
    )


@pytest.fixture
def mlwh_lh_samples_multiple(app, mlwh_sql_engine):
    insert_into_mlwh(
        app, MLWH_LH_SAMPLES_MULTIPLE, mlwh_sql_engine, app.config["MLWH_LIGHTHOUSE_SAMPLE_TABLE"]
    )


@pytest.fixture
def mlwh_sentinel_cherrypicked(app, mlwh_sql_engine):
    def delete_data():
        delete_from_mlwh(app, mlwh_sql_engine, app.config["MLWH_STOCK_RESOURCES_TABLE"])
        delete_from_mlwh(app, mlwh_sql_engine, app.config["MLWH_SAMPLE_TABLE"])
        delete_from_mlwh(app, mlwh_sql_engine, app.config["MLWH_STUDY_TABLE"])

    try:
        delete_data()

        # inserts
        insert_into_mlwh(
            app,
            MLWH_SAMPLE_STOCK_RESOURCE["sample"],
            mlwh_sql_engine,
            app.config["MLWH_SAMPLE_TABLE"],
        )
        insert_into_mlwh(
            app,
            MLWH_SAMPLE_STOCK_RESOURCE["study"],
            mlwh_sql_engine,
            app.config["MLWH_STUDY_TABLE"],
        )
        insert_into_mlwh(
            app,
            MLWH_SAMPLE_STOCK_RESOURCE["stock_resource"],
            mlwh_sql_engine,
            app.config["MLWH_STOCK_RESOURCES_TABLE"],
        )

        yield
    finally:
        delete_data()


@pytest.fixture
def mlwh_beckman_cherrypicked(app, mlwh_sql_engine):
    def delete_data():
        delete_from_mlwh(app, mlwh_sql_engine, app.config["MLWH_SAMPLE_TABLE"])
        delete_from_mlwh(app, mlwh_sql_engine, app.config["MLWH_LIGHTHOUSE_SAMPLE_TABLE"])

    try:
        delete_data()

        # inserts
        insert_into_mlwh(
            app,
            MLWH_SAMPLE_LIGHTHOUSE_SAMPLE["lighthouse_sample"],
            mlwh_sql_engine,
            app.config["MLWH_LIGHTHOUSE_SAMPLE_TABLE"],
        )
        insert_into_mlwh(
            app,
            MLWH_SAMPLE_LIGHTHOUSE_SAMPLE["sample"],
            mlwh_sql_engine,
            app.config["MLWH_SAMPLE_TABLE"],
        )

        yield
    finally:
        delete_data()


@pytest.fixture
def mlwh_sentinel_and_beckman_cherrypicked(app, mlwh_sql_engine):
    def delete_data():
        delete_from_mlwh(app, mlwh_sql_engine, app.config["MLWH_STOCK_RESOURCES_TABLE"])
        delete_from_mlwh(app, mlwh_sql_engine, app.config["MLWH_SAMPLE_TABLE"])
        delete_from_mlwh(app, mlwh_sql_engine, app.config["MLWH_STUDY_TABLE"])
        delete_from_mlwh(app, mlwh_sql_engine, app.config["MLWH_LIGHTHOUSE_SAMPLE_TABLE"])

    try:
        delete_data()

        # inserts
        insert_into_mlwh(
            app,
            MLWH_SAMPLE_LIGHTHOUSE_SAMPLE["lighthouse_sample"],
            mlwh_sql_engine,
            app.config["MLWH_LIGHTHOUSE_SAMPLE_TABLE"],
        )
        insert_into_mlwh(
            app,
            MLWH_SAMPLE_STOCK_RESOURCE["sample"] + MLWH_SAMPLE_LIGHTHOUSE_SAMPLE["sample"],
            mlwh_sql_engine,
            app.config["MLWH_SAMPLE_TABLE"],
        )
        insert_into_mlwh(
            app,
            MLWH_SAMPLE_STOCK_RESOURCE["study"],
            mlwh_sql_engine,
            app.config["MLWH_STUDY_TABLE"],
        )
        insert_into_mlwh(
            app,
            MLWH_SAMPLE_STOCK_RESOURCE["stock_resource"],
            mlwh_sql_engine,
            app.config["MLWH_STOCK_RESOURCES_TABLE"],
        )

        yield
    finally:
        delete_data()


def insert_into_mlwh(app, data, mlwh_sql_engine, table_name):
    table = get_table(mlwh_sql_engine, table_name)

    with mlwh_sql_engine.begin() as connection:
        connection.execute(table.delete())  # delete all rows from table first
        print("Inserting MLWH test data")
        connection.execute(table.insert(), data)


def delete_from_mlwh(app, mlwh_sql_engine, table_name):
    table = get_table(mlwh_sql_engine, table_name)

    with mlwh_sql_engine.begin() as connection:
        print("Deleting MLWH test data")
        connection.execute(table.delete())


@pytest.fixture
def event_wh_data(app, event_wh_sql_engine):
    try:
        subjects_table = get_table(event_wh_sql_engine, app.config["EVENT_WH_SUBJECTS_TABLE"])
        roles_table = get_table(event_wh_sql_engine, app.config["EVENT_WH_ROLES_TABLE"])
        events_table = get_table(event_wh_sql_engine, app.config["EVENT_WH_EVENTS_TABLE"])
        event_types_table = get_table(event_wh_sql_engine, app.config["EVENT_WH_EVENT_TYPES_TABLE"])
        subject_types_table = get_table(
            event_wh_sql_engine, app.config["EVENT_WH_SUBJECT_TYPES_TABLE"]
        )
        role_types_table = get_table(event_wh_sql_engine, app.config["EVENT_WH_ROLE_TYPES_TABLE"])

        def delete_event_warehouse_data():
            with event_wh_sql_engine.begin() as connection:
                connection.execute(roles_table.delete())
                connection.execute(subjects_table.delete())
                connection.execute(events_table.delete())
                connection.execute(event_types_table.delete())
                connection.execute(subject_types_table.delete())
                connection.execute(role_types_table.delete())

        delete_event_warehouse_data()

        with event_wh_sql_engine.begin() as connection:
            print("Inserting Events Warehouse test data")
            connection.execute(role_types_table.insert(), EVENT_WH_DATA["role_types"])
            connection.execute(event_types_table.insert(), EVENT_WH_DATA["event_types"])
            connection.execute(subject_types_table.insert(), EVENT_WH_DATA["subject_types"])
            connection.execute(subjects_table.insert(), EVENT_WH_DATA["subjects"])
            connection.execute(events_table.insert(), EVENT_WH_DATA["events"])
            connection.execute(roles_table.insert(), EVENT_WH_DATA["roles"])

        yield
    finally:
        delete_event_warehouse_data()


@pytest.fixture
def mlwh_sql_engine(app):
    return create_mysql_connection_engine(
        app.config["WAREHOUSES_RW_CONN_STRING"], app.config["MLWH_DB"]
    )


@pytest.fixture
def dart_connection(app):
    return create_dart_connection()


@pytest.fixture
def dart_schema_create(app):
    with app.app_context():
        load_sql_server_script(app, "tests/data/dart/schema.sql")


@pytest.fixture
def dart_seed_reset(app, dart_schema_create):
    with app.app_context():
        load_sql_server_script(app, "tests/data/dart/seed.sql")


@pytest.fixture
def dart_samples_for_bp_test(app, dart_schema_create):
    with app.app_context():
        load_sql_server_script(app, "tests/data/dart/seed_for_bp_test.sql")


@pytest.fixture
def dart_mongo_merged_samples():
    return DART_MONGO_MERGED_SAMPLES


@pytest.fixture
def samples_with_lab_id(app):
    with app.app_context():
        samples_collection = app.data.driver.db.samples
        _ = samples_collection.insert_many(SAMPLES_WITH_LAB_ID)

    #  yield a copy of that the test change it however it wants
    yield copy.deepcopy(SAMPLES)

    # clear up after the fixture is used
    with app.app_context():
        samples_collection.delete_many({})


@pytest.fixture
def event_wh_sql_engine(app):
    return create_mysql_connection_engine(
        app.config["WAREHOUSES_RW_CONN_STRING"], app.config["EVENTS_WH_DB"]
    )


@pytest.fixture
def samples_with_uuids(app):
    with app.app_context():
        samples_collection = app.data.driver.db.samples
        _ = samples_collection.insert_many(SAMPLES_WITH_UUIDS)

    #  yield a copy of that the test change it however it wants
    yield copy.deepcopy(SAMPLES_WITH_UUIDS)

    # clear up after the fixture is used
    with app.app_context():
        samples_collection.delete_many({})


@pytest.fixture
def message_unknown():
    message_content = {
        "event": {
            "uuid": "1770dbcd-0abf-4293-ac62-dd26964f80b0",
            "event_type": "no_callbacks",
            "occured_at": "2020-11-26T15:58:20",
            "user_identifier": "test1",
            "subjects": [],
            "metadata": {},
        },
        "lims": "LH_TEST",
    }
    return Message(message_content)


@pytest.fixture
def message_source_complete():
    message_content = {
        "event": {
            "uuid": "1770dbcd-0abf-4293-ac62-dd26964f80b0",
            "event_type": PLATE_EVENT_SOURCE_COMPLETED,
            "occured_at": "2020-11-26T15:58:20",
            "user_identifier": "test1",
            "subjects": [
                {
                    "role_type": "sample",
                    "subject_type": "sample",
                    "friendly_name": "friendly_name",
                    "uuid": "00000000-1111-2222-3333-555555555555",
                },
                {
                    "role_type": "cherrypicking_source_labware",
                    "subject_type": "plate",
                    "friendly_name": "plate-barcode",
                    "uuid": "00000000-1111-2222-3333-555555555556",
                },
                {
                    "role_type": "robot",
                    "subject_type": "robot",
                    "friendly_name": "robot-serial",
                    "uuid": "00000000-1111-2222-3333-555555555557",
                },
            ],
            "metadata": {},
        },
        "lims": "LH_TEST",
    }
    return Message(message_content)


@pytest.fixture
def message_source_all_negative():
    message_content = {
        "event": {
            "uuid": "1770dbcd-0abf-4293-ac62-dd26964f80b0",
            "event_type": PLATE_EVENT_SOURCE_ALL_NEGATIVES,
            "occured_at": "2020-11-26T15:58:20",
            "user_identifier": "test1",
            "subjects": [
                {
                    "role_type": "cherrypicking_source_labware",
                    "subject_type": "plate",
                    "friendly_name": "plate-barcode",
                    "uuid": "00000000-1111-2222-3333-555555555556",
                },
                {
                    "role_type": "robot",
                    "subject_type": "robot",
                    "friendly_name": "robot-serial",
                    "uuid": "00000000-1111-2222-3333-555555555557",
                },
            ],
            "metadata": {},
        },
        "lims": "LH_TEST",
    }
    return Message(message_content)
