CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    legal_name VARCHAR(200),
    tax_id VARCHAR(13) UNIQUE,
    email VARCHAR(150),
    phone VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Entidad intermedia: permite que un usuario pertenezca a varias empresas
CREATE TABLE company_users (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES companies(id),
    user_id INT NOT NULL REFERENCES users(id),
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (company_id, user_id)
);

-- Regla de negocio: un solo administrador principal por empresa
CREATE UNIQUE INDEX one_admin_per_company
    ON company_users (company_id)
    WHERE is_admin;
