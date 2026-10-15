# SPDX-FileCopyrightText: 2016-2020 CERN.
# SPDX-License-Identifier: MIT

"""Extended Date(/Time) Format Level 0 date string field."""

from datetime import MAXYEAR, MINYEAR

from babel_edtf import parse_edtf
from edtf import (
    Date,
    DateAndTime,
    Interval,
    Level1Interval,
    Level2Interval,
    OneOfASet,
    UncertainOrApproximate,
)
from marshmallow import ValidationError, fields
from marshmallow.validate import Validator
from pyparsing import ParseException


class EDTFValidator(Validator):
    """EDTF validator."""

    default_message = "Please provide a valid date or interval."

    def __init__(
        self,
        types=[Date, DateAndTime, Interval],
        chronological_interval=True,
        error=None,
    ):
        """Constructor.

        :params types: List of EDTFObject subclasses that you accept.
        """
        self._types = types or []
        self._chronological_interval = chronological_interval
        self._error = error or self.default_message

    def _format_error(self, value, e):
        return self._error.format(input=value, edtf=e)

    def __call__(self, value):
        """Validate."""
        try:
            e = parse_edtf(value)
        except ParseException:
            raise ValidationError(self._format_error(value, None))

        # Open or unknown intervals are Level 1
        # They subclass Interval, so the type check below would let them through
        if isinstance(e, Level1Interval):
            raise ValidationError(self._format_error(value, e))

        if self._types:
            if not any([isinstance(e, t) for t in self._types]):
                raise ValidationError(self._format_error(value, e))

        lower, upper = e.lower_strict(), e.upper_strict()

        # babel-edtf formats through Python's datetime
        # Negative years and 0000 cannot be parsed
        if not (
            MINYEAR <= lower.tm_year <= MAXYEAR and MINYEAR <= upper.tm_year <= MAXYEAR
        ):
            raise ValidationError(self._format_error(value, e))

        if self._chronological_interval:
            # We require intervals to be chronological. EDTF Date and Interval
            # both have same interface and
            # date.lower_strict() <= date.upper_strict() is always True for a
            # Date
            if upper < lower:
                raise ValidationError(self._format_error(value, e))

        return value


class EDTFDateString(fields.Str):
    """
    Extended Date Format Level 0 date string field.

    A string field which is using the EDTF Validator.
    """

    def __init__(self, **kwargs):
        """Constructor."""
        kwargs.setdefault("validate", EDTFValidator(types=[Date, Interval]))
        super().__init__(**kwargs)


class EDTFDateTimeString(fields.Str):
    """
    Extended Date(/Time) Format Level 0 date string field.

    A string field which is using the EDTF Validator.
    """

    def __init__(self, **kwargs):
        """Constructor."""
        kwargs.setdefault("validate", EDTFValidator())
        super().__init__(**kwargs)


class EDTFLevel2DateString(fields.Str):
    """
    Extended Date Format Level 2 date string field.

    A string field which is using the EDTF Validator.
    """

    def __init__(self, **kwargs):
        """Constructor."""
        kwargs.setdefault(
            "validate",
            EDTFValidator(
                types=[
                    Date,
                    Interval,
                    Level1Interval,
                    UncertainOrApproximate,
                    OneOfASet,
                    Level2Interval,
                ]
            ),
        )
        super().__init__(**kwargs)
