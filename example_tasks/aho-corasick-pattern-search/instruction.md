A log analysis system needs to efficiently search log files for hundreds of keywords simultaneously. Implement a multi-pattern search engine.

Sample log data is available at `/app/input_files/log_samples.txt` and search keywords at `/app/input_files/keywords.txt`.

A scaffold file is provided at `/app/input_files/log_search.py`. Complete the implementation and place the finished file at `/app/log_search.py`.

## Complexity Requirement

- Linear time O(n + m + k) where n=text length, m=total pattern length, k=matches
- Handle overlapping matches