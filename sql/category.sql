-- =============================================================
-- 分类表：首页/分类页的商品分类（热销爆款、食堂套餐、奶茶饮品等）
-- =============================================================
CREATE TABLE `category` (
    `id`          INT UNSIGNED    NOT NULL AUTO_INCREMENT COMMENT '分类ID',
    `code`        VARCHAR(32)     NOT NULL                COMMENT '分类标识：hot/canteen/drink 等',
    `name`        VARCHAR(50)     NOT NULL                COMMENT '分类名称',
    `emoji`       VARCHAR(16)     NOT NULL DEFAULT ''     COMMENT '分类图标',
    `tint`        VARCHAR(16)     NOT NULL DEFAULT ''     COMMENT '主题底色，如 #EAF3DE',
    `sort`        INT             NOT NULL DEFAULT 0      COMMENT '排序值，越小越靠前',
    `status`      TINYINT         NOT NULL DEFAULT 1      COMMENT '状态：1显示 0隐藏',
    `is_deleted`  TINYINT(1)      NOT NULL DEFAULT 0      COMMENT '是否删除：0未删除 1已删除',
    `create_time` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_category_code` (`code`),
    KEY `idx_category_sort` (`sort`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '商品分类表';
