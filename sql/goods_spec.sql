-- =============================================================
-- 商品规格表：一个商品多种可选规格（辣度、冰量、尺寸、口味等）
-- =============================================================
CREATE TABLE `goods_spec` (
    `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '规格ID',
    `goods_id`      BIGINT UNSIGNED NOT NULL                COMMENT '所属商品ID',
    `spec_name`     VARCHAR(50)     NOT NULL                COMMENT '规格名称，如 微辣 / 少冰 / 1.5m',
    `price`         DECIMAL(10, 2)  NOT NULL                COMMENT '规格售价',
    `origin_price`  DECIMAL(10, 2)  NOT NULL DEFAULT 0.00   COMMENT '规格原价',
    `stock`         INT             NOT NULL DEFAULT 0      COMMENT '规格库存',
    `sort`          INT             NOT NULL DEFAULT 0      COMMENT '排序值，越小越靠前',
    `status`        TINYINT         NOT NULL DEFAULT 1      COMMENT '状态：1启用 0停用',
    `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0      COMMENT '是否删除：0未删除 1已删除',
    `create_time`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_goods_spec_goods` (`goods_id`),
    CONSTRAINT `fk_goods_spec_goods` FOREIGN KEY (`goods_id`) REFERENCES `goods` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '商品规格表';
