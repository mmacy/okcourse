# Contribute to `okcourse`

You're encouraged to contribute your awesome code and doc skills to the `okcourse` project. Set up your dev environment and get hacking!

## Prerequisites

- Experience with [Python](https://docs.python.org/3.12/tutorial/index.html) and [Markdown](https://www.markdownguide.org/) or a healthy curiousity and ability to "learn by doing."

    The `okcourse` codebase uses Python features up to and including those in [Python 3.12](https://docs.python.org/3.12/).

- Credentials for an AI model service provider's API.

    [OpenAI](https://platform.openai.com/docs/quickstart) is the first provider supported by `okcourse`, so that's a good one to start with unless you're adding support for a new model provider.

## Install uv

[Install uv](https://docs.astral.sh/uv/getting-started/installation/) by Astral if you don't already have it.

Though not strictly required to contribute to `okcourse`, many people find using `uv` to work with Python projects *much* easier than with other tools. In fact, `uv` will even [install Python](https://docs.astral.sh/uv/guides/install-python/) for you!

You are welcome to use `python -m venv`, Poetry, or another tool to create and manage your Python environments, but this project uses `uv`and so will these instructions.

## Get the code and docs

1. Fork the [mmacy/okcourse repository](https://github.com/mmacy/okcourse) on GitHub.
1. Clone your fork with `git` and then enter the cloned repo's root directory:

    ```sh
    # Clone your fork of the repo with SSH
    git clone git@github.com:USER/okcourse.git

    # Enter repo root dir
    cd okcourse
    ```

    Replace `USER` with your GitHub username.

## Enable AI model access

The `okcourse` library looks for API credentials in an environment variable when creating the API client. The credentials are typically an API key that grant the client access to the AI service provider's models.

!!! warning

    The API key owner is responsible for any API usage fees incurred by using that key to generate content with the `okcourse` library.

Using `okcourse` to generate course content may cost you, your employer, or whomever owns the API key real money. The library doesn't yet support locally hosted AI models, so until you or I add that support, you'll likely be paying someone to use their models.

After you've forked and cloned the repo, set the environment variable required by your AI model provider.

| AI model provider | Set this environment variable |
| :---------------: | :---------------------------: |
|      OpenAI       |       `OPENAI_API_KEY`        |
|     Anthropic     |      *not yet supported*      |
|      Google       |      *not yet supported*      |
|  Locally hosted   |      *not yet supported*      |

## Contribute code

Create a branch, write some code in your favorite editor, push it to your fork, and open a PR in the upstream [mmacy/okcourse](https://github.com/mmacy/okcourse) repo.

This project aspires to adhere to the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) and Pythonic coding principles, the latter of which are as follows:

```console
$ uv run python
Python 3.12.7 (main, Oct 16 2024, 07:12:08) [Clang 18.1.8 ] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import this
The Zen of Python, by Tim Peters

Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
>>>
```

## Contribute documentation

To contribute to `okcourse` documentation, you should be able to stage and view the docs locally.

Install the dependencies required by [mkdocs-material](https://github.com/squidfunk/mkdocs-material) with `uv`:

```sh
# Install doc dependencies
uv sync --group docs
```

Start the local hot reload-enabled web server:

```sh
# Start MkDocs built-in webserver
uv run mkdocs serve
```

And finally, navigate to the `Serving on ...` URL in the output and add or edit docs, verifying they look OK along the way.

```console hl_lines="10"
$ uv run mkdocs serve
INFO    -  Building documentation...
INFO    -  git-committers plugin ENABLED
INFO    -  git-committers: found page authors cache file - loading it
INFO    -  Cleaning site directory
INFO    -  git-committers: fetching contributors for docs/roadmap.md
INFO    -  git-committers: saving page authors cache file
INFO    -  Documentation built in 6.80 seconds
INFO    -  [16:28:08] Watching paths for changes: 'docs', 'mkdocs.yml', 'README.md', 'src/okcourse', 'examples'
INFO    -  [16:28:08] Serving on http://127.0.0.1:8000/okcourse/
```

The documentation should appear in your browser, similar to the following:

![A screenshot of the okcourse documentation homepage as rendered locally in a web browser. The page includes navigation links to sections like 'Examples' and 'API Reference,' a table of contents sidebar, and sample code demonstrating how to generate course content. The design features a clean layout with a dark theme.][docs-staging-local-01]

[docs-staging-local-01]: https://raw.githubusercontent.com/mmacy/okcourse/1467e9366bd996fc6fa76cac941226d56f2a4796/images/docs-staging-local-01.png
