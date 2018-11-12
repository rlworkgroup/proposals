Continuous Benchmarking System
======
Kevin Cheng
Initial Proposal 11/6/18


# Background:
## Context
Benchmarking an algorithm is a compute intensive and time consuming chore that is essential for guaranteeing performance. 
An algorithm can unknowingly drift towards an undesirable state if the laborious task of benchmarking is neglected for
too long.  

## Problem Statement
We want to create a continous benchmarking system to automate this task.  

## Scope
Problem starts with a code changes to Garage. The system needs to run benchmarking at least nightly, generate a results page, and deploy that page.  Problem ends with a pubically viewable results page.


## Goals and Non-Goals
*This version of the proposal will focus on a minimally viable system. These goals will evolve once the initial goal is accomplished and we decide to bring in more complexity.
#### Goals:
- Update benchmarking scripts so they can be started in a consistent format and run to completion without manual intervention.
- Focus on getting system up and running on a single machine.
- Design a simple system for deploying the results page.
- Allow garage developers to detect regressions in algorithm performance caused by code changes

#### Non-Goals: 
- Worry about scalability too early.  MVP is top priority.
- Design for frugality over simplicity
- Manage web servers

## Design Overview
*The input and output interfaces of the benchmarking scripts must be normalized (start commands, and results).
This initial design will use a cron job script ran on a single local machine. On a nightly basis the script shall:
1. pull the latest garage code.
2. Run commands to launch benchmarking jobs
3. Detect when the jobs are completed
4. Run script to generate results page with plots.
5. Deploy results.html to Github pages or similar.


## Detailed Design (skip for now)
Component-by-component sections, data, etc., as relevant to the particular system. These should include sketches of credible implementation plans mentioning specific technologies. They don't need to be so detailed that they are equivalent to writing the code.

## Additional Resources Needed (skip for now)
What new machines, people, money, etc. are needed to complete implementation?

## Cross-Cutting Concerns (skip for now)
How your design affects other teams or parts of the software. Very project-specific. This includes API changes you might need, disruptions of others' work, etc.

## Alternatives Considered:

The local cron job solution was proposed because of the compute limitations in available CI services.
#### Travis CI.
The current CI tool to manage the workflow of building garage and executing unit tests.  The Travis CI build 
environment have a maximum of 7.5 GB of memory, and 2 cores.  It also limits jobs to 120 minutes maximum for a
private Github repo, and 50 minutes for a public Github repo.  
https://docs.travis-ci.com/user/customizing-the-build/
https://docs.travis-ci.com/user/reference/overview/

#### Github Actions
Each workflow can run for up to 58 minutes (including queuing and execution time).  Two workflows can be running 
concurrently per repository.  1 virtual CPU.  Up to 3.75 GB of memory
https://developer.github.com/actions/creating-workflows/workflow-configuration-options/

Another local solution   
#### TeamCity/Jenkins
These tools provide the same workflow management features that we would implement in our cron job.  However, the initial setup of these tools may be too great for the purposes of our minimal viable product.  We can consider bringing in these tools in the next iteration of the system, or if our home-grown solutions proves to be unmaintable/unreliable.

For deploying webpages:
There are a lot of options here.
#### Amazon S3 
May cost around $0.50 cents per month.  Github pages would require us to commit/push our results into a repo, which might be more complicated than Amazons workflow.
    
