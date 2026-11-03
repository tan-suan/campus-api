-- =============================================================
-- 优惠券表：满减券（满 20 减 3、满 35 减 6、满 60 减 12 等）
-- =============================================================
CREATE TABLE `coupon` (
    `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '优惠券ID',
    `code`         VARCHAR(32)     NOT NULL                COMMENT '优惠券编码',
    `name`         VARCHAR(50)     NOT NULL                COMMENT '券名称，如 满 20 减 3',
    `threshold`    DECIMAL(10, 2)  NOT NULL DEFAULT 0.00   COMMENT '使用门槛金额，0 表示无门槛',
    `amount`       DECIMAL(10, 2)  NOT NULL DEFAULT 0.00   COMMENT '减免金额',
    `scope`        VARCHAR(50)     NOT NULL DEFAULT '全场通用' COMMENT '适用范围',
    `description`  VARCHAR(255)    NOT NULL DEFAULT ''     COMMENT '使用说明',
    `total`        INT             NOT NULL DEFAULT 0      COMMENT '发行总量，0 表示不限量',
    `received`     INT             NOT NULL DEFAULT 0      COMMENT '已领取数量',
    `start_time`   DATETIME        NULL                    COMMENT '生效时间，空表示立即生效',
    `end_time`     DATETIME        NULL                    COMMENT '失效时间，空表示长期有效',
    `status`       TINYINT         NOT NULL DEFAULT 1      COMMENT '状态：1可用 0停用',
    `is_deleted`   TINYINT(1)      NOT NULL DEFAULT 0      COMMENT '是否删除：0未删除 1已删除',
    `create_time`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_coupon_code` (`code`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '优惠券表';
