# fan_out

A lambda function that fires whenever a batch of Kinesis events drops to S3. This function fans out the events from the centralized Kinesis bucket into individual user's buckets. Events get partitioned by `event_type` and time. The time partitioning is amenable to Glue crawlers and Athena queries.
