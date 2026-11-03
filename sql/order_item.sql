-- =============================================================
-- 订单明细表：下单时的商品快照（名称、规格、成交价不随商品改价变化）
-- =============================================================
CREATE TABLE `order_item` (
    `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '明细ID',
    `order_id`       BIGINT UNSIGNED NOT NULL                COMMENT '所属订单ID',
    `goods_id`       BIGINT UNSIGNED NOT NULL                COMMENT '商品ID',
    `goods_spec_id`  BIGINT UNSIGNED NULL                    COMMENT '规格ID',
    `goods_name`     VARCHAR(200)    NOT NULL                COMMENT '商品名称快照',
    `spec_name`      VARCHAR(50)     NOT NULL DEFAULT '默认' COMMENT '规格名称快照',
    `emoji`          VARCHAR(16)     NOT NULL DEFAULT ''     COMMENT '商品图标快照',
    `tint`           VARCHAR(16)     NOT NULL DEFAULT ''     COMMENT '图标底色快照',
    `price`          DECIMAL(10, 2)  NOT NULL                COMMENT '成交单价',
    `origin_price`   DECIMAL(10, 2)  NOT NULL DEFAULT 0.00   COMMENT '原价',
    `qty`            INT             NOT NULL DEFAULT 1      COMMENT '购买数量',
    `subtotal`       DECIMAL(10, 2)  NOT NULL DEFAULT 0.00   COMMENT '小计金额',
    `is_deleted`     TINYINT(1)      NOT NULL DEFAULT 0      COMMENT '是否删除：0未删除 1已删除',
    `create_time`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_order_item_order` (`order_id`),
    KEY `idx_order_item_goods` (`goods_id`),
    CONSTRAINT `fk_order_item_order` FOREIGN KEY (`order_id`) REFERENCES `order` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_order_item_goods` FOREIGN KEY (`goods_id`) REFERENCES `goods` (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '订单明细表';
