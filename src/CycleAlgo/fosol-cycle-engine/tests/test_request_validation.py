"""Tests for §14.2 request validation and the §14.3 error contract."""

import json
import unittest

from src.error_contract import build_error_response, http_status_for_error
from src.request_validation import (
    DEFAULT_PREFERENCE,
    DEFAULT_WATER_ACCESS,
    MAX_START_DATE,
    MIN_START_DATE,
    PREFERENCE_VALUES,
    WATER_ACCESS_VALUES,
    RequestValidationError,
    validate_explore_request,
)

KNOWN_CROP_IDS = {"crop_one", "crop_two"}


def make_payload(**overrides: object) -> dict:
    payload = {
        "district_id": "rajshahi",
        "start_date": "2026-11-06",
        "first_crop_id": None,
    }
    payload.update(overrides)
    return payload


class RequestValidationTests(unittest.TestCase):
    def assert_invalid(self, payload: object, field: str | None) -> RequestValidationError:
        with self.assertRaises(RequestValidationError) as caught:
            validate_explore_request(payload, KNOWN_CROP_IDS)
        exc = caught.exception
        self.assertEqual(exc.code, "INVALID_REQUEST")
        self.assertEqual(exc.field, field)
        self.assertTrue(exc.message)
        return exc

    def test_minimal_payload_applies_documented_defaults(self) -> None:
        result = validate_explore_request(make_payload(), KNOWN_CROP_IDS)
        self.assertEqual(
            result,
            {
                "district_id": "rajshahi",
                "start_date": "2026-11-06",
                "first_crop_id": None,
                "water_access": DEFAULT_WATER_ACCESS,
                "preference": DEFAULT_PREFERENCE,
            },
        )
        self.assertEqual(result["water_access"], "unknown")
        self.assertEqual(result["preference"], "fastest_completion")

    def test_full_payload_round_trips(self) -> None:
        payload = make_payload(
            first_crop_id="crop_one",
            water_access="irrigation_available",
            preference="more_crop_diversity",
        )
        self.assertEqual(validate_explore_request(payload, KNOWN_CROP_IDS), payload)

    def test_every_allowed_enum_value_is_accepted(self) -> None:
        for water_access in WATER_ACCESS_VALUES:
            for preference in PREFERENCE_VALUES:
                with self.subTest(
                    water_access=water_access, preference=preference
                ):
                    result = validate_explore_request(
                        make_payload(
                            water_access=water_access, preference=preference
                        ),
                        KNOWN_CROP_IDS,
                    )
                    self.assertEqual(result["water_access"], water_access)
                    self.assertEqual(result["preference"], preference)

    def test_unknown_extra_keys_are_ignored(self) -> None:
        result = validate_explore_request(
            make_payload(unknown_key="ignored", another_unknown=123),
            KNOWN_CROP_IDS,
        )
        self.assertEqual(
            result, validate_explore_request(make_payload(), KNOWN_CROP_IDS)
        )

    def test_district_id_missing_blank_or_non_string(self) -> None:
        missing = make_payload()
        missing.pop("district_id")
        for label, payload in (
            ("missing", missing),
            ("empty", make_payload(district_id="")),
            ("blank", make_payload(district_id="   ")),
            ("null", make_payload(district_id=None)),
            ("number", make_payload(district_id=7)),
            ("boolean", make_payload(district_id=True)),
            ("list", make_payload(district_id=["rajshahi"])),
        ):
            with self.subTest(case=label):
                self.assert_invalid(payload, "district_id")

    def test_bad_start_dates_are_rejected(self) -> None:
        for value in (
            "2026-02-30",
            "2026-1-6",
            "06-11-2026",
            "2026-13-01",
            "2026-11-6",
            "2026-11-06T00:00:00",
            "",
            20261106,
            None,
            True,
        ):
            with self.subTest(value=value):
                self.assert_invalid(make_payload(start_date=value), "start_date")

        missing = make_payload()
        missing.pop("start_date")
        error = self.assert_invalid(missing, "start_date")
        self.assertEqual(error.message, "start_date is required.")

    def test_bad_date_message_matches_spec_example(self) -> None:
        error = self.assert_invalid(
            make_payload(start_date="2026-02-30"), "start_date"
        )
        self.assertEqual(
            error.message, "start_date must be a valid YYYY-MM-DD date."
        )

    def test_real_calendar_dates_including_leap_day_are_accepted(self) -> None:
        result = validate_explore_request(
            make_payload(start_date="2024-02-29"), KNOWN_CROP_IDS
        )
        self.assertEqual(result["start_date"], "2024-02-29")
        self.assert_invalid(make_payload(start_date="2026-02-29"), "start_date")

    def test_planning_date_limits_leave_room_for_calendar_calculations(self) -> None:
        for value in ("0001-01-01", "9991-01-01", "9998-01-01", "9999-12-31"):
            with self.subTest(value=value):
                self.assert_invalid(make_payload(start_date=value), "start_date")
        for value in (MIN_START_DATE, MAX_START_DATE):
            with self.subTest(value=value):
                result = validate_explore_request(
                    make_payload(start_date=value), KNOWN_CROP_IDS
                )
                self.assertEqual(result["start_date"], value)

    def test_first_crop_id_null_is_accepted(self) -> None:
        result = validate_explore_request(make_payload(), KNOWN_CROP_IDS)
        self.assertIsNone(result["first_crop_id"])

    def test_first_crop_id_must_be_null_or_a_known_id(self) -> None:
        for value in (
            "crop_unknown",
            "",
            " crop_one",
            7,
            True,
            ["crop_one"],
            {"id": "crop_one"},
        ):
            with self.subTest(value=value):
                self.assert_invalid(
                    make_payload(first_crop_id=value), "first_crop_id"
                )

        missing = make_payload()
        missing.pop("first_crop_id")
        error = self.assert_invalid(missing, "first_crop_id")
        self.assertEqual(error.message, "first_crop_id is required.")

    def test_water_access_rejects_every_invalid_value(self) -> None:
        for value in (
            None,
            "",
            "not_sure",
            "irrigation",
            "RAINFED",
            "unknown ",
            0,
            True,
            [],
            {"value": "unknown"},
        ):
            with self.subTest(value=value):
                self.assert_invalid(
                    make_payload(water_access=value), "water_access"
                )

    def test_preference_rejects_every_invalid_value(self) -> None:
        for value in (
            None,
            "",
            "cheapest",
            "FASTEST_COMPLETION",
            "fastest completion",
            "lowest_upfront_cash",
            0,
            True,
            [],
            {"value": "fastest_completion"},
        ):
            with self.subTest(value=value):
                self.assert_invalid(make_payload(preference=value), "preference")

    def test_lowest_upfront_cash_is_rejected_until_cash_flow_exists(self) -> None:
        self.assertNotIn("lowest_upfront_cash", PREFERENCE_VALUES)
        self.assert_invalid(
            make_payload(preference="lowest_upfront_cash"), "preference"
        )

    def test_payload_must_be_a_json_object(self) -> None:
        for value in (None, [], "request", 7, True):
            with self.subTest(value=value):
                self.assert_invalid(value, None)


class ErrorContractTests(unittest.TestCase):
    def _validation_error(self) -> RequestValidationError:
        with self.assertRaises(RequestValidationError) as caught:
            validate_explore_request(
                make_payload(start_date="2026-02-30"), KNOWN_CROP_IDS
            )
        return caught.exception

    def test_error_response_has_exact_documented_shape(self) -> None:
        response = build_error_response(self._validation_error())
        self.assertEqual(
            response,
            {
                "schema_version": "1",
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "start_date must be a valid YYYY-MM-DD date.",
                    "field": "start_date",
                },
            },
        )
        self.assertEqual(response["schema_version"], "1")
        self.assertEqual(set(response), {"schema_version", "error"})
        self.assertEqual(
            set(response["error"]), {"code", "message", "field"}
        )
        self.assertIsInstance(json.dumps(response), str)

    def test_whole_payload_error_has_null_field(self) -> None:
        with self.assertRaises(RequestValidationError) as caught:
            validate_explore_request([], KNOWN_CROP_IDS)
        response = build_error_response(caught.exception)
        self.assertIsNone(response["error"]["field"])
        self.assertIsInstance(json.dumps(response), str)

    def test_invalid_request_maps_to_http_400(self) -> None:
        self.assertEqual(http_status_for_error(self._validation_error()), 400)

    def test_unexpected_error_maps_to_http_500(self) -> None:
        self.assertEqual(http_status_for_error(RuntimeError("boom")), 500)


if __name__ == "__main__":
    unittest.main()
