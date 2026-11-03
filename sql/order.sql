-- =============================================================
-- 订单主表：状态 pending/picking/done/canceled，取货方式 pickup/dorm
-- 注意：order 为 MySQL 保留字，读写时必须使用反引号
-- =============================================================
CREATE TABLE `order` (
    `id`                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '订单ID',
    `order_no`          VARCHAR(32)     NOT NULL                COMMENT '订单号，如 CF20260926100821',
    `user_id`           BIGINT UNSIGNED NOT NULL                COMMENT '下单用户ID',
    `status`            ENUM ('pending', 'picking', 'done', 'canceled') NOT NULL DEFAULT 'pending'
                                                                COMMENT '订单状态：pending待付款 picking待取货 done已完成 canceled已取消',
    `mode`              ENUM ('pickup', 'dorm') NOT NULL DEFAULT 'pickup'
                                                                COMMENT '取货方式：pickup校内自提 dorm送到寝室',
    `pickup_point_id`   INT UNSIGNED    NULL                    COMMENT '自提点ID（自提时）',
    `pickup_point_name` VARCHAR(100)    NOT NULL DEFAULT ''     COMMENT '自提点名称快照',
    `address_id`        BIGINT UNSIGNED NULL                    COMMENT '收货地址ID（送寝时）',
    `address_text`      VARCHAR(255)    NOT NULL DEFAULT ''     COMMENT '收货地址快照',
    `pickup_code`       VARCHAR(16)     NOT NULL DEFAULT ''     COMMENT '取货码，如 A-1088',
    `expect_time`       VARCHAR(50)     NOT NULL DEFAULT '尽快送达' COMMENT '期望时间文案',
    `goods_total`       DECIMAL(10, 2)  NOT NULL DEFAULT 0.00   COMMENT '商品金额',
    `freight`           DECIMAL(10, 2)  NOT NULL DEFAULT 0.00   COMMENT '配送费',
    `discount`          DECIMAL(10, 2)  NOT NULL DEFAULT 0.00   COMMENT '优惠减免',
    `pay_amount`        DECIMAL(10, 2)  NOT NULL DEFAULT 0.00   COMMENT '实付金额',
    `coupon_id`         BIGINT UNSIGNED NULL                    COMMENT '使用的优惠券ID',
    `pay_method`        VARCHAR(20)     NOT NULL DEFAULT '微信支付' COMMENT '支付方式',
    `remark`            VARCHAR(255)    NOT NULL DEFAULT ''     COMMENT '订单备注',
    `goods_count`       INT             NOT NULL DEFAULT 0      COMMENT '商品总件数',
    `pay_time`          DATETIME        NULL                    COMMENT '支付时间',
    `done_time`         DATETIME        NULL                    COMMENT '完成时间',
    `cancel_time`       DATETIME        NULL                    COMMENT '取消时间',
    `is_deleted`        TINYINT(1)      NOT NULL DEFAULT 0      COMMENT '是否删除：0未删除 1已删除',
    `create_time`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_no` (`order_no`),
    KEY `idx_order_user_status` (`user_id`, `status`),
    KEY `idx_order_pickup_point` (`pickup_point_id`),
    KEY `idx_order_address` (`address_id`),
    KEY `idx_order_coupon` (`coupon_id`),
    CONSTRAINT `fk_order_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
    CONSTRAINT `fk_order_pickup_point` FOREIGN KEY (`pickup_point_id`) REFERENCES `pickup_point` (`id`),
    CONSTRAINT `fk_order_address` FOREIGN KEY (`address_id`) REFERENCES `address` (`id`),
    CONSTRAINT `fk_order_coupon` FOREIGN KEY (`coupon_id`) REFERENCES `coupon` (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '订单表';
