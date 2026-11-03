-- =============================================================
-- 用户表：校园闪购小程序用户（微信登录 + 校园卡余额）
-- =============================================================
CREATE TABLE `user` (
    `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `openid`      VARCHAR(64)     NOT NULL                COMMENT '微信 openid',
    `nickname`    VARCHAR(50)     NOT NULL DEFAULT ''     COMMENT '昵称',
    `avatar`      VARCHAR(255)    NOT NULL DEFAULT ''     COMMENT '头像地址',
    `phone`       VARCHAR(20)     NOT NULL DEFAULT ''     COMMENT '手机号',
    `gender`      TINYINT         NOT NULL DEFAULT 0      COMMENT '性别：0未知 1男 2女',
    `campus`      VARCHAR(50)     NOT NULL DEFAULT ''     COMMENT '所在校区',
    `balance`     DECIMAL(10, 2)  NOT NULL DEFAULT 0.00   COMMENT '校园卡余额',
    `status`      TINYINT         NOT NULL DEFAULT 1      COMMENT '状态：1正常 0禁用',
    `is_deleted`  TINYINT(1)      NOT NULL DEFAULT 0      COMMENT '是否删除：0未删除 1已删除',
    `create_time` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_openid` (`openid`),
    KEY `idx_user_phone` (`phone`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户表';
