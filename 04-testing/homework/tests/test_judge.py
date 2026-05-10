import pytest
from tests.utils import run_agent_test
from tests.judge import assert_criteria

# @pytest.mark.skip(reason='only run the additional tests')
async def test_agent_performance(agent):
    user_prompt = "Which hour of the day has the highest average fare amount"
    result = await run_agent_test(agent, user_prompt)

    await assert_criteria(result, [
        "the SQL query correctly calculates average fare by hour of day",
        "the result identifies a specific hour as having the highest average fare",
        "the result includes the actual average fare amount"
    ])


async def test_zero_passenger_trip_count(agent):
    user_prompt = "How many trips had zero passengers recorded?"
    result = await run_agent_test(agent, user_prompt)

    await assert_criteria(result, [
        "the SQL query filters trips where passenger_count = 0 and counts them",
        "the get_schema tool should be called first followed by the run_sql tool",
        "the result should contain this specific value: 31465"
    ])


async def test_average_tip_credit_card(agent):
    user_prompt = "What is the average tip amount for credit card payments?"
    result = await run_agent_test(agent, user_prompt)

    await assert_criteria(result, [
        "the get_schema tool should be called first followed by the run_sql tool",
        "the SQL query filters by credit card payments using the payment_type column",
        "the SQL query calculates the average of the tip_amount column",
        "the result contains a value close to 4.17"
    ])


async def test_busiest_pickup_location(agent):
    user_prompt = "Which pickup location (PULocationID) has the most trips?"
    result = await run_agent_test(agent, user_prompt)

    await assert_criteria(result, [
        "the get_schema tool should be called first followed by the run_sql tool",
        "the SQL query groups by PULocationID and counts trips",
        "the SQL query orders by trip count descending to find the highest",
        "the result identifies PULocationID 132 as having the most trips with 145240 trips"
    ])


async def test_average_fare_long_trips(agent):
    user_prompt = "What is the average fare for trips longer than 10 miles?"
    result = await run_agent_test(agent, user_prompt)

    await assert_criteria(result, [
        "the get_schema tool should be called first followed by the run_sql tool",
        "the SQL query filters trips where trip_distance > 10",
        "the SQL query calculates the average of the fare_amount column",
        "the result contains a value close to 62.88"
    ])


async def test_busiest_day_of_week(agent):
    user_prompt = "What is the busiest day of the week for taxi trips?"
    result = await run_agent_test(agent, user_prompt)

    await assert_criteria(result, [
        "the get_schema tool should be called first followed by the run_sql tool",
        "the SQL query extracts the day of week from the pickup datetime column",
        "the SQL query counts trips grouped by day of week",
        "the result identifies Wednesday (or day 3) as the busiest day with 495032 trips"
    ])
