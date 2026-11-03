-- =============================================================
-- 商品表：闪购商品（含秒杀、热销标识与软删除）
-- =============================================================
CREATE TABLE `goods` (
    `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '商品ID',
    `goods_no`      VARCHAR(32)     NOT NULL                COMMENT '商品编号',
    `name`          VARCHAR(200)    NOT NULL                COMMENT '商品名称',
    `category_id`   INT UNSIGNED    NOT NULL                COMMENT '分类ID',
    `price`         DECIMAL(10, 2)  NOT NULL                COMMENT '闪购价',
    `origin_price`  DECIMAL(10, 2)  NOT NULL DEFAULT 0.00   COMMENT '原价',
    `stock`         INT             NOT NULL DEFAULT 0      COMMENT '剩余库存',
    `total_stock`   INT             NOT NULL DEFAULT 0      COMMENT '总库存（用于展示抢购进度）',
    `sold`          INT             NOT NULL DEFAULT 0      COMMENT '已售数量',
    `emoji`         VARCHAR(16)     NOT NULL DEFAULT ''     COMMENT '商品图标（原型占位图）',
    `tint`          VARCHAR(16)     NOT NULL DEFAULT ''     COMMENT '图标底色',
    `main_image`    VARCHAR(255)    NOT NULL DEFAULT ''     COMMENT '商品主图地址',
    `tag`           VARCHAR(50)     NOT NULL DEFAULT ''     COMMENT '角标文案，如 秒杀价',
    `summary`       VARCHAR(255)    NOT NULL DEFAULT ''     COMMENT '一句话描述',
    `detail`        TEXT                                    COMMENT '商品详情',
    `flash`         TINYINT(1)      NOT NULL DEFAULT 0      COMMENT '是否秒杀：0否 1是',
    `hot`           TINYINT(1)      NOT NULL DEFAULT 0      COMMENT '是否热销：0否 1是',
    `sort`          INT             NOT NULL DEFAULT 0      COMMENT '排序值，越小越靠前',
    `status`        TINYINT         NOT NULL DEFAULT 1      COMMENT '状态：1上架 0下架',
    `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0      COMMENT '是否删除：0未删除 1已删除',
    `create_time`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_goods_no` (`goods_no`),
    KEY `idx_goods_category` (`category_id`),
    KEY `idx_goods_flash` (`flash`),
    KEY `idx_goods_hot` (`hot`),
    KEY `idx_goods_status` (`status`),
    CONSTRAINT `fk_goods_category` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '商品表';
