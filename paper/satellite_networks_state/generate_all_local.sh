num_threads=1

# Specify the workload IDs you want to run
workload_ids_to_run="71"

# Loop over specified workload IDs
for i in ${workload_ids_to_run}
do
  time bash generate_for_paper.sh ${i} ${num_threads} || exit 1
done


#for i in 2 5 8 11 14 1 4 7 10 13 0 3 6 9 12
#do
#  bash generate_for_paper.sh ${i} ${num_threads} || exit 1
#done
