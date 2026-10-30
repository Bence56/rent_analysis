# Data pipeline and CI/CD

## Data lineage

The Spark Declarative Pipeline loads both sources and derives bronze, silver,
and gold materialized views. The gold tables are published to the configured
catalog and schema, where the manager dashboard reads them as datasets.

```mermaid
flowchart LR
    AirbnbSource["Airbnb CSV<br/>Unity Catalog volume"]
    KamernetSource["Kamernet JSON<br/>Unity Catalog volume"]

    BronzeAirbnb["bronze_airbnb<br/>CSV ingestion"]
    BronzeKamernet["bronze_kamernet<br/>JSON ingestion"]

    SilverAirbnb["silver_airbnb<br/>cast, filter, normalize ZIP<br/>fill missing review score"]
    SilverKamernet["silver_kamernet<br/>parse amounts, cast, normalize"]

    Combined["Align and union<br/>Airbnb + Kamernet properties"]
    Revenue["Gold: revenue_per_property<br/>annual and 5-year estimates"]
    DistrictStats["Gold: property_statistics_per_district<br/>postal-code price statistics"]
    DashboardRevenue["Dashboard dataset<br/>revenue_per_property"]
    DashboardDistricts["Dashboard dataset<br/>property_statistics_per_district"]
    Dashboard["Rent analysis manager's Dashboard"]

    AirbnbSource --> BronzeAirbnb --> SilverAirbnb
    KamernetSource --> BronzeKamernet --> SilverKamernet
    SilverAirbnb --> Combined
    SilverKamernet --> Combined
    Combined --> Revenue
    Combined --> DistrictStats
    Revenue --> DashboardRevenue --> Dashboard
    DistrictStats --> DashboardDistricts --> Dashboard
```

## CI/CD pipeline

The `checks` job runs for pull requests, pushes to `main`, and manual
`workflow_dispatch` runs. Deployment waits for checks to pass and is restricted
to `main` pushes or manual runs on `main`.

```mermaid
flowchart TD
    PR["Pull request"] --> Checkout
    PushMain["Push to main"] --> Checkout
    Manual["Manual workflow_dispatch"] --> Checkout

    Checkout["Checkout source"] --> Python["Set up Python 3.12"]
    Python --> UV["Set up uv"]
    UV --> Sync["uv sync --locked --dev"]
    Sync --> Hooks["uv run pre-commit run --all-files<br/>Includes tests with 80% coverage minimum"]

    Hooks --> Gate{"Checks pass?"}
    Gate -->|No| Stop["Workflow ends"]
    Gate -->|Yes| DeployCondition{"Push to main<br/>or manual run on main?"}
    DeployCondition -->|No| Done["Checks complete"]
    DeployCondition -->|Yes| Auth["OAuth M2M credentials<br/>from databricks-dev environment"]
    Auth --> CLI["Set up Databricks CLI"]
    CLI --> Bundle["databricks bundle deploy --target dev"]
```
