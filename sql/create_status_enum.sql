CREATE TYPE public."Status" AS ENUM
    ('Ciphered', 'Ready', 'Submitted');

ALTER TYPE public."Status"
    OWNER TO root;
