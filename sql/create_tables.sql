CREATE TABLE public."cake-db"
(
    "ID" integer NOT NULL,
    "Process_id" text NOT NULL,
    "File" bytea[] NOT NULL,
    "From" text NOT NULL,
    "Policy" text,
    "Entries" text,
    "IPFS link" text,
    "Slices" text,
    "Message_id" text,
    "TX_ID" text,
    "Status" "Status",
    PRIMARY KEY ("ID")
);

ALTER TABLE IF EXISTS public."cake-db"
    OWNER to root;