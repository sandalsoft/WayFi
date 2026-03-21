"""Tests for SMS notification service."""

from __future__ import annotations

from wayfi.notify.sms import parse_room_reply


class TestRoomReplyParsing:
    def test_simple_room_number(self):
        result = parse_room_reply("1412")
        assert result is not None
        assert result.room_number == "1412"
        assert result.nights == 1

    def test_room_with_nights(self):
        result = parse_room_reply("1412, 3 nights")
        assert result is not None
        assert result.room_number == "1412"
        assert result.nights == 3

    def test_room_prefix(self):
        result = parse_room_reply("room 1412")
        assert result is not None
        assert result.room_number == "1412"

    def test_short_nights(self):
        result = parse_room_reply("1412 3n")
        assert result is not None
        assert result.room_number == "1412"
        assert result.nights == 3

    def test_for_nights(self):
        result = parse_room_reply("1412 for 2 nights")
        assert result is not None
        assert result.room_number == "1412"
        assert result.nights == 2

    def test_room_with_letter(self):
        result = parse_room_reply("12A")
        assert result is not None
        assert result.room_number == "12A"

    def test_no_room_number(self):
        result = parse_room_reply("hello")
        assert result is None

    def test_single_night_default(self):
        result = parse_room_reply("305")
        assert result is not None
        assert result.nights == 1

    def test_case_insensitive(self):
        result = parse_room_reply("Room 1412, 3 Nights")
        assert result is not None
        assert result.room_number == "1412"
        assert result.nights == 3
