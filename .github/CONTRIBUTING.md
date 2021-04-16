# Contributing to SlowMovie
We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## Getting Started

Before jumping right into making a new issue please see if you've tried the following: 

1. Go through the [README](https://github.com/TomWhitwell/SlowMovie/blob/main/README.md) and make sure you're following the steps exactly
2. Search [current Issues](https://github.com/TomWhitwell/SlowMovie/issues) and see if this is a known problem, perhaps even being worked on already.

## Opening An Issue
We use GitHub issues to track issues. Report a something by [opening a new issue](https://github.com/TomWhitwell/SlowMovie/issues); it's that easy! There are a few templates to choose from, pick the one that works best for your situation: 

* __Bug__ - choose this if you're having trouble getting things working or things just aren't working as you expect
* __Feature Request__ - request something new be added. 
* __Informational__ - have a comment or something that just doesn't fit the other two categories, try this. 

### Pay attention to the details!

**Great** Bug Reports tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

A thorough bug report is your best chance things can be fixed quickly. 

## Pull Requests
Pull requests are the best way to propose changes to the codebase (we use [Github Flow](https://guides.github.com/introduction/flow/index.html)). We actively welcome your pull requests:

1. Fork the repo and create your branch from the one you want to make changes to (usually `main`).
2. If you've changed functionality or dependencies, update the documentation.
3. Submit that pull request! Be sure to include relevant information per the PR template. 


### Coding Standards
For code consistancy we try our best to adhere to the [PEP8](https://www.python.org/dev/peps/pep-0008/) guide. This makes sure everything looks cohesive regardless of who did the actually coding. All PRs will automatically be checked before review or merging. Don't let this scare you from contributing! These are often minor changes and Maintainers can help if this is a sticking point. 

Before submitting a PR you can check your code yourself by installing [Flake8](https://flake8.pycqa.org/en/latest/) and running a simple command.

```
pip3 install flake8
flake8 --ignore E501 slowmovie.py
```

### Review Process
Once submitted your PR will get reviewed - be patient.

* All pull requests require at least one approval review from a maintainer before being merged.
* For larger changes that modify base functionality, multiple reviewers should test and discuss the changes before merging the PR.

It may take some time and back and forth to get things all squared away. You may even be asked to change something, it's all part of the process.

Once everything looks good your PR will be merged!

## License
When you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.
