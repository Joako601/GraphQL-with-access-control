
-- ---------- Día 1: cuentas ----------

CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES companies(id),
    account_type VARCHAR(20) NOT NULL
        CHECK (account_type IN ('DEBIT', 'CREDIT', 'CASH', 'SAVINGS', 'INVESTMENT', 'WALLET', 'OTHER')),
    name VARCHAR(150) NOT NULL,
    bank_name VARCHAR(150),
    account_number VARCHAR(20),
    clabe VARCHAR(18),
    card_last_digits VARCHAR(4),
    short_description VARCHAR(255),
    long_description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE (id, company_id)
);

-- Una empresa no puede tener dos cuentas con el mismo nombre
CREATE UNIQUE INDEX IF NOT EXISTS accounts_company_name_unique
    ON accounts (company_id, LOWER(name));

-- Una CLABE identifica una sola cuenta bancaria 
CREATE UNIQUE INDEX IF NOT EXISTS accounts_clabe_unique
    ON accounts (clabe)
    WHERE clabe IS NOT NULL;


-- ---------- Día 1: conceptos ----------

CREATE TABLE IF NOT EXISTS concepts (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES companies(id),
    concept_type VARCHAR(10) NOT NULL CHECK (concept_type IN ('INCOME', 'EXPENSE')),
    name VARCHAR(150) NOT NULL,
    short_description VARCHAR(255),
    long_description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (id, company_id)
);

-- Una empresa no puede tener dos conceptos con el mismo nombre 
CREATE UNIQUE INDEX IF NOT EXISTS concepts_company_name_unique
    ON concepts (company_id, LOWER(name));


-- ---------- Día 1: conceptos permitidos por cuenta (N:M) ----------

CREATE TABLE IF NOT EXISTS account_concepts (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    account_id INT NOT NULL,
    concept_id INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (account_id, concept_id),
    FOREIGN KEY (account_id, company_id) REFERENCES accounts (id, company_id),
    FOREIGN KEY (concept_id, company_id) REFERENCES concepts (id, company_id)
);


-- ---------- Día 2: movimientos ----------

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    account_id INT NOT NULL,
    concept_id INT NOT NULL,
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('INCOME', 'EXPENSE')),
    amount NUMERIC(14, 2) NOT NULL CHECK (amount > 0),
    transaction_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    captured_by INT NOT NULL REFERENCES users(id),
    short_description VARCHAR(255),
    long_description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
    FOREIGN KEY (account_id, company_id) REFERENCES accounts (id, company_id),
    FOREIGN KEY (concept_id, company_id) REFERENCES concepts (id, company_id),

    FOREIGN KEY (account_id, concept_id) REFERENCES account_concepts (account_id, concept_id),

    FOREIGN KEY (company_id, captured_by) REFERENCES company_users (company_id, user_id)
);

CREATE INDEX IF NOT EXISTS transactions_account_idx
    ON transactions (account_id, transaction_date DESC);
