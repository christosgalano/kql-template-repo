# Notes

## Phase 1

folder config:

- order of execution
- ignore
- include
- action(s) on results:
  - print
  - github summary
  - email (recipient, from github user or github bot)

  - github issue
  - slack:
  - ...

### 1. kql-template-repo

```pseudocode
For each query q in folder:
  results = execute(q)
  if len(results) == 0:
    print("No results for query: " + q)
  else:
    for r in results:
      print(r)
```

### 2. threat-hunting-template-repo

```pseudocode
For each query q in folder:
  results = execute(q)
  if len(results) == 0:
    print("No results for query: " + q)
  else:
    for r in results:
      take_action(r)
```

### 3. threat-hunting-baseline

instantiation of the template and fill with existing material

---

## Phase 2

Add file config capability with:

- kql query - content
- parsing rules for results
- action to take on results
- output format
