-- =============================================================
-- 收货地址表：送给寝室时使用的宿舍地址，按用户隔离
-- =============================================================
CREATE TABLE `address` (
    `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '地址ID',
    `user_id`        BIGINT UNSIGNED NOT NULL                COMMENT '所属用户ID',
    `receiver_name`  VARCHAR(50)     NOT NULL                COMMENT '收货人姓名',
    `phone`          VARCHAR(20)     NOT NULL                COMMENT '收货人手机号',
    `campus`         VARCHAR(50)     NOT NULL DEFAULT ''     COMMENT '校区',
    `building`       VARCHAR(100)    NOT NULL                COMMENT '楼栋，如 梅园 7 号楼',
    `detail`         VARCHAR(100)    NOT NULL DEFAULT ''     COMMENT '门牌，如 305 室',
    `is_default`     TINYINT(1)      NOT NULL DEFAULT 0      COMMENT '是否默认地址：0否 1是',
    `status`         TINYINT         NOT NULL DEFAULT 1      COMMENT '状态：1有效 0停用',
    `is_deleted`     TINYINT(1)      NOT NULL DEFAULT 0      COMMENT '是否删除：0未删除 1已删除',
    `create_time`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_address_user` (`user_id`),
    CONSTRAINT `fk_address_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '收货地址表';
