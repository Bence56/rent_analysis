# rent_analysis

The 'rent_analysis' project as RevoData take home assesment.
* `dashboards`: The Dashboard json file.
* `data`: Exported data in parquet format.
* `docs`: Diagrams for pipeline and CI/CD.
* `src/`: Python source code for this project.
  * `src/rent_analysis/`: Shared Python code that can be used by jobs and pipelines.
* `resources/`:  Resource configurations (jobs, pipelines, etc.)
* `scratch/`:  Exploratory notebooks.
* `tests/`: Unit tests for the shared Python code.
* `fixtures/`: Fixtures for data sets (primarily used for testing).


## Getting started

Choose how you want to work on this project:

(a) Directly in your Databricks workspace, see
    https://docs.databricks.com/dev-tools/bundles/workspace.

(b) Locally with an IDE like Cursor or VS Code, see
    https://docs.databricks.com/dev-tools/vscode-ext.html.

(c) With command line tools, see https://docs.databricks.com/dev-tools/cli/databricks-cli.html

If you're developing with an IDE, dependencies for this project should be installed using uv:

*  Make sure you have the UV package manager installed.
   It's an alternative to tools like pip: https://docs.astral.sh/uv/getting-started/installation/.
*  Run `uv sync --dev` to install the project's dependencies.

## GitHub Actions CI/CD

The CI/CD workflow runs every configured pre-commit hook on pull requests and
pushes to `main`. The pytest hook enforces at least 80% test coverage. On pushes
to `main` (and manual runs from `main`), it also builds the wheel and deploys
the Databricks bundle to the `dev` target.

### Configure Databricks service-principal authentication

The deployment uses Databricks OAuth machine-to-machine (M2M) authentication
for the service principal. It does not require an account-level federation
policy.

1. Make sure the service principal is added to the target Databricks workspace
   and has the workspace, bundle-resource, and Unity Catalog permissions needed
   for deployment.
2. Create an OAuth secret for the service principal in Databricks. Record its
   application/client ID and the secret value when it is displayed; the secret
   value may not be viewable again.
3. In GitHub **Settings → Environments**, create an environment named
   `databricks-dev` and restrict deployments to the `main` branch.
4. In that environment, set:
   * **Variable** `DATABRICKS_HOST` =
     `https://dbc-45bf58f8-78cd.cloud.databricks.com`
   * **Secret** `DATABRICKS_CLIENT_ID` = the service principal's application ID
   * **Secret** `DATABRICKS_CLIENT_SECRET` = the OAuth secret value
5. Push to `main` or run **CI/CD** manually from `main`. The deploy job runs
   only after the checks pass.

See the [Databricks OAuth M2M guide](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m)
for service-principal OAuth setup details.


# Using this project using the CLI

The Databricks workspace and IDE extensions provide a graphical interface for working
with this project. It's also possible to interact with it directly using the CLI:

1. Authenticate to your Databricks workspace, if you have not done so already:
    ```
    $ databricks configure
    ```

2. To deploy a development copy of this project, type:
    ```
    $ databricks bundle deploy --target dev
    ```
    (Note that "dev" is the default target, so the `--target` parameter
    is optional here.)

    This deploys everything that's defined for this project.
    For example, the default template would deploy a pipeline called
    `[dev yourname] rent_analysis_etl` to your workspace.
    You can find that resource by opening your workpace and clicking on **Jobs & Pipelines**.

3. Similarly, to deploy a production copy, type:
   ```
   $ databricks bundle deploy --target prod
   ```
   Note the default template has a includes a job that runs the pipeline every day
   (defined in resources/sample_job.job.yml). The schedule
   is paused when deploying in development mode (see
   https://docs.databricks.com/dev-tools/bundles/deployment-modes.html).

4. To run a job or pipeline, use the "run" command:
   ```
   $ databricks bundle run
   ```

5. Finally, to run tests locally, use `pytest`:
   ```
   $ uv run pytest
   ```

# Medallion architecture
## Prerequsites
I uploaded the source data files to a new catalog called technical. All of the loaders use <code>overwrite</code> mode, for this use case this is adequate. In a real life scenario we must use <code>append</code> mode and apply a CDC statistics and an upsert merge logic to avoid data duplication.

## Bronze layer

I designed two tasks one for Airbnb data, and one for Kamernet. Both bronze table is a one of one version of the raw data as a Delta table. No coluns are dropped, all columns are strings.

## Silver layer
Generally, I wanted to create the silver layer to have a clear business data, so more data products could use it, for example for ML use cases.
### Airbnb

After type conversions I filtered out the one obvious outlier addressed in the exploratory notebook.


Cleaned the ZIP codes to be stored as 4 numbers and 2 letters with no space between. Didn't filterd out any occurences because they didn't fit the format because I wanted to have the opportunity to later fill the incomplete zip codes. Unfortunatelly I did not understand the implementation the AI gave me, so I did not include it to the project. That would be the next feature to develop for sure, I tried to add the most value possible to the asset bundle.


Filled the review scores with the median score of reviews.


I have missed checking the duplications, that is a mistake.

### Kamernet

First I removed the EUR symbols and the extra spaces from all the columns that stored an amount of money. By this way we could convert them into numeric columns, which are easier to use for calculations.


The next step was type conversion and filling the None values in the numeric columns.


The last step was selecting only the useful columns, which are storing business values. I dropped technical or metadata columns from the crawler.

## Gold layer

Generally the gold layer is ment to be aggregated data and the reporting tools should only read them and not make any aggregations.

I designed two tables. The first one should answer the question of every property, and calculate the revenue.

The second one contains some statistics of the districts.

# pre-commit

Checks I implemented:
- Dock strings
- 80% unit test code coverage
- typehinting

# CI/CD pipeline

Standard pipeline for github actions, runs the checks, builds the artifact and deploys it to Databricks when a PR is merged to main.
