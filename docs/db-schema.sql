-- ------------------------------------
-- Project: Online Bookstore (MySQL / 13-Table 3NF)
-- Database Type: MySQL
-- Design Principle:
-- Fully normalized (3NF) schema.
-- 'likes' table is split into 'review_likes' and 'comment_likes'
-- for full referential integrity.
-- ------------------------------------

-- Drop tables if exist (in reverse dependency order)
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS library_items;
DROP TABLE IF EXISTS wishlist_items;
DROP TABLE IF EXISTS cart_items;
DROP TABLE IF EXISTS comment_likes;
DROP TABLE IF EXISTS review_likes;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS book_categories;
DROP TABLE IF EXISTS book_authors;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS authors;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------
-- 1. User Table
-- ------------------------------------
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_users_email (email),
    INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 2. Book Table
-- ------------------------------------
CREATE TABLE books (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    isbn VARCHAR(13) NOT NULL UNIQUE,
    cover_image_url VARCHAR(255),
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    publication_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL COMMENT 'For soft delete',

    INDEX idx_books_title (title),
    INDEX idx_books_isbn (isbn),
    INDEX idx_books_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 3. Author Table
-- ------------------------------------
CREATE TABLE authors (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_authors_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 4. Category Table
-- ------------------------------------
CREATE TABLE categories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_categories_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 5. Book-Author Junction Table
-- ------------------------------------
CREATE TABLE book_authors (
    book_id BIGINT NOT NULL,
    author_id BIGINT NOT NULL,

    PRIMARY KEY (book_id, author_id),

    CONSTRAINT fk_book_authors_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_book_authors_author
        FOREIGN KEY (author_id) REFERENCES authors(id)
        ON DELETE CASCADE,

    INDEX idx_book_authors_author (author_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 6. Book-Category Junction Table
-- ------------------------------------
CREATE TABLE book_categories (
    book_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,

    PRIMARY KEY (book_id, category_id),

    CONSTRAINT fk_book_categories_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_book_categories_category
        FOREIGN KEY (category_id) REFERENCES categories(id)
        ON DELETE CASCADE,

    INDEX idx_book_categories_category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 7. Review Table
-- ------------------------------------
CREATE TABLE reviews (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    book_id BIGINT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_reviews_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_reviews_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE,

    INDEX idx_reviews_user_book (user_id, book_id),
    INDEX idx_reviews_book (book_id),
    INDEX idx_reviews_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 8. Comment Table
-- ------------------------------------
CREATE TABLE comments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    book_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_comments_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_comments_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE,

    INDEX idx_comments_user (user_id),
    INDEX idx_comments_book (book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 9. Review Likes Table
-- ------------------------------------
CREATE TABLE review_likes (
    user_id BIGINT NOT NULL,
    review_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, review_id),

    CONSTRAINT fk_review_likes_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_review_likes_review
        FOREIGN KEY (review_id) REFERENCES reviews(id)
        ON DELETE CASCADE,

    INDEX idx_review_likes_review (review_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 10. Comment Likes Table
-- ------------------------------------
CREATE TABLE comment_likes (
    user_id BIGINT NOT NULL,
    comment_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, comment_id),

    CONSTRAINT fk_comment_likes_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_comment_likes_comment
        FOREIGN KEY (comment_id) REFERENCES comments(id)
        ON DELETE CASCADE,

    INDEX idx_comment_likes_comment (comment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 11. Cart Items Table
-- ------------------------------------
CREATE TABLE cart_items (
    user_id BIGINT NOT NULL,
    book_id BIGINT NOT NULL,
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, book_id),

    CONSTRAINT fk_cart_items_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_cart_items_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE,

    INDEX idx_cart_items_book (book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 12. Wishlist Items Table
-- ------------------------------------
CREATE TABLE wishlist_items (
    user_id BIGINT NOT NULL,
    book_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, book_id),

    CONSTRAINT fk_wishlist_items_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_wishlist_items_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE,

    INDEX idx_wishlist_items_book (book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 13. Library Items Table
-- ------------------------------------
CREATE TABLE library_items (
    user_id BIGINT NOT NULL,
    book_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp of acquisition',

    PRIMARY KEY (user_id, book_id),

    CONSTRAINT fk_library_items_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_library_items_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE RESTRICT,

    INDEX idx_library_items_book (book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 14. Orders Table
-- ------------------------------------
CREATE TABLE orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL CHECK (total_price >= 0),
    status ENUM('pending', 'paid', 'shipped', 'delivered', 'cancelled') NOT NULL DEFAULT 'pending',
    shipping_address TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_orders_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT,

    INDEX idx_orders_user (user_id),
    INDEX idx_orders_status (status),
    INDEX idx_orders_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- 15. Order Items Table
-- ------------------------------------
CREATE TABLE order_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    book_id BIGINT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    price_at_purchase DECIMAL(10, 2) NOT NULL CHECK (price_at_purchase >= 0),

    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id) REFERENCES orders(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_order_items_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE RESTRICT,

    UNIQUE INDEX idx_order_items_order_book (order_id, book_id),
    INDEX idx_order_items_order (order_id),
    INDEX idx_order_items_book (book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------
-- Summary: 15 Tables Created
-- ------------------------------------
-- 1. users
-- 2. books
-- 3. authors
-- 4. categories
-- 5. book_authors (junction)
-- 6. book_categories (junction)
-- 7. reviews
-- 8. comments
-- 9. review_likes
-- 10. comment_likes
-- 11. cart_items
-- 12. wishlist_items
-- 13. library_items
-- 14. orders
-- 15. order_items
-- ------------------------------------
