-- UUID 생성용
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- 벡터 검색용
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash TEXT NOT NULL,
    profile_image_s3_key TEXT,
    profile_prompt TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    failed_login_count INT DEFAULT 0,
    locked_until TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

--하루1개 정책 강제
CREATE TABLE diaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    diary_date DATE NOT NULL,
    content TEXT NOT NULL,
    image_s3_key TEXT,
    mood TEXT,
    style_preset VARCHAR(50),
    generation_options JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT unique_user_date UNIQUE (user_id, diary_date)
);

CREATE INDEX idx_diaries_user ON diaries(user_id);
--일기 분할 저장 테이블
CREATE TABLE diary_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    diary_id UUID NOT NULL REFERENCES diaries(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    token_count INT,
    start_char INT,
    end_char INT,
    embedding_status VARCHAR(20) DEFAULT 'pending',
    last_embedded_at TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT unique_chunk_order UNIQUE (diary_id, chunk_index)
);

CREATE INDEX idx_chunks_user ON diary_chunks(user_id);
CREATE INDEX idx_chunks_diary ON diary_chunks(diary_id);

--search table
CREATE TABLE diary_chunk_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID NOT NULL REFERENCES diary_chunks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    embedding VECTOR(1536) NOT NULL,
    embedding_model TEXT NOT NULL,
    embedding_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT unique_chunk_model UNIQUE (chunk_id, embedding_model, embedding_version)
);
--HNSW 인덱스 
CREATE INDEX idx_embeddings_vector
ON diary_chunk_embeddings
USING hnsw (embedding vector_cosine_ops);

--사용자 스코프 필터링용
CREATE INDEX idx_embeddings_user ON diary_chunk_embeddings(user_id);