-- =============================================================
-- 购物车表：按「用户 + 商品 + 规格」唯一，同一规格重复加购只累加数量
-- =============================================================
CREATE TABLE `cart` (
    `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '购物车条目ID',
    `user_id`        BIGINT UNSIGNED NOT NULL                COMMENT '所属用户ID',
    `goods_id`       BIGINT UNSIGNED NOT NULL                COMMENT '商品ID',
    `goods_spec_id`  BIGINT UNSIGNED NULL                    COMMENT '规格ID，空表示默认规格',
    `spec_name`      VARCHAR(50)     NOT NULL DEFAULT '默认' COMMENT '规格名称快照',
    `qty`            INT             NOT NULL DEFAULT 1      COMMENT '购买数量',
    `selected`       TINYINT(1)      NOT NULL DEFAULT 1      COMMENT '是否勾选结算：0否 1是',
    `create_time`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_cart_user_goods_spec` (`user_id`, `goods_id`, `goods_spec_id`),
    KEY `idx_cart_goods` (`goods_id`),
    KEY `idx_cart_spec` (`goods_spec_id`),
    CONSTRAINT `fk_cart_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_cart_goods` FOREIGN KEY (`goods_id`) REFERENCES `goods` (`id`),
    CONSTRAINT `fk_cart_goods_spec` FOREIGN KEY (`goods_spec_id`) REFERENCES `goods_spec` (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '购物车表';
