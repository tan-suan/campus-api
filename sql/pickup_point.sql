-- =============================================================
-- 自提点表：校内自提的取货地点（菜鸟驿站、自提柜、服务台等）
-- =============================================================
CREATE TABLE `pickup_point` (
    `id`             INT UNSIGNED  NOT NULL AUTO_INCREMENT COMMENT '自提点ID',
    `name`           VARCHAR(100)  NOT NULL                COMMENT '自提点名称',
    `business_hours` VARCHAR(50)   NOT NULL DEFAULT ''     COMMENT '营业时间，如 08:00 - 21:00',
    `distance_desc`  VARCHAR(50)   NOT NULL DEFAULT ''     COMMENT '距离描述，如 步行 3 分钟',
    `address`        VARCHAR(255)  NOT NULL DEFAULT ''     COMMENT '详细位置',
    `contact_phone`  VARCHAR(20)   NOT NULL DEFAULT ''     COMMENT '联系电话',
    `sort`           INT           NOT NULL DEFAULT 0      COMMENT '排序值，越小越靠前',
    `status`         TINYINT       NOT NULL DEFAULT 1      COMMENT '状态：1启用 0停用',
    `is_deleted`     TINYINT(1)    NOT NULL DEFAULT 0      COMMENT '是否删除：0未删除 1已删除',
    `create_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_pickup_point_sort` (`sort`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '自提点表';
