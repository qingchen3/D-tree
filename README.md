

*******
 About 
*******
  
  This package contains source codes for our experiments. All results shown in our
  paper are reproducible.


*********************************
 Install python3 and dependencies	 
*********************************
 
 a) install Python3
 
 b) install dependencies
    run `pip3 install -r requirements.text`
 
 
********************
 Reproducing results
********************

  Reproducing the results reported in our paper. All results are stored in the folder "res". 
  
  - To reproduce results for Figure 10, run "python3 evaluate_insertion_only.py testcase", 
  where testcase is one of ["eron", "tech", "stackoverflow", "youtube"] .
    - Examples: python3 evaluate_insertion_only.py enron, python3 evaluate_insertion_only.py tech. 
    - Output: res/insertiononly_query.csv, res/insertiononly_update.csv
  
  - To reproduce the results for Figure 11(a), run "python3 diameter_dist.py". 
    - Output: res/diameter_dist.dat
  
  - To reproduce the results for Figure 11(b), run "python3 avg_sp.py".   
    - Output: res/avg_sp.dat
  
  - Reproducing the results for Figure 12, Figure 13 and Figure 14 needs to run two different pipelines for Semantic 
  Scholar graph and all others since Semantic Scholar is more larger than others. Everything about Semantic Scholar
  graphs can not fit in 500 GB memory. We store the workloads for Semantic graphs on the disks, and we evaluate
  D-tree, nD-tree and HK separately. 
    - run "python3 evaluate.py testcase", where testcase is one of ["dnc", "call", "messages", "wiki", "fb", 
    "eron", "tech", "stackoverflow", "youtube"]. 
        - Examples: "python3 evaluate.py fb", "python3 evaluate.py youtube".  
        - Outputs are explained below.  
     - run "python3 evaluate_scholar_Dtree.py scholar" for evaluating D-tree, 
     run "python3 evaluate_scholar_nDtree.py scholar" for evaluating nD-tree, 
     run "python3 evaluate_scholar_HK.py scholar" for evaluating HK,  
    - Output: Results are saved in files and printed on terminal.
        -  Results saved in files. In the folder "res", 
            file Sd_*.csv contains results of Sd for each data set(shown in Figure 12);
            distributions of distance for each data set (shown in Figure 16 in the technical report) 
            are located the folder "res/dist/, with each sub folder for each data set;
            file query_*.csv contains results of query performance(shown in Figure 13) for each data set;
            file insertion_nte.csv contains results of inserting non-tree edges operation (shown in Figure 14);
            file insertion_te.csv contains results of inserting tree edges operation (shown in Figure 14);
            file deletion_nte.csv contains results of deleting non-tree edges operation (shown in Figure 14);
            file deletion_te.csv contains results of deleting tree edges operation (shown in Figure 14).
  
        - Results on terminal. Results for inserting non-tree edges, 
          inserting tree edges, deleting non-tree edge, deleting tree edges, S_d and query 
          performance are shown at each testing point.
  
  
  To see how inefficient ET and opt are for large graph, run "python supplementary.py".
