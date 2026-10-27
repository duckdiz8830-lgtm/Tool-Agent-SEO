<?php
// 1) WordPress > WPCode > Add Snippet > PHP Snippet; nếu editor đã có PHP mode thì copy từ dòng add_action xuống, không copy dòng <?php.
// 2) Chọn Auto Insert / Run Everywhere rồi Activate; snippet chỉ in schema khi đang ở trang WooCommerce product.
// 3) Mở sản phẩm > View Source, tìm '"@type":"Product"'; nếu bài có FAQ thì tìm thêm '"@type":"FAQPage"'. Không thấy thì tắt snippet và báo lại.

add_action('wp_head', function () {
    if (!function_exists('is_product') || !is_product()) {
        return;
    }

    $post_id = get_queried_object_id();
    if (!$post_id) {
        return;
    }

    $keys = array('_snl_schema_jsonld', '_snl_faq_schema_jsonld');
    foreach ($keys as $key) {
        $schema = get_post_meta($post_id, $key, true);
        if (!$schema) {
            continue;
        }

        if (is_string($schema)) {
            $decoded = json_decode($schema, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                continue;
            }
            $schema = $decoded;
        }

        if (!is_array($schema) && !is_object($schema)) {
            continue;
        }

        $json = wp_json_encode(
            $schema,
            JSON_UNESCAPED_UNICODE
            | JSON_UNESCAPED_SLASHES
            | JSON_HEX_TAG
            | JSON_HEX_AMP
            | JSON_HEX_APOS
            | JSON_HEX_QUOT
        );
        if (!$json) {
            continue;
        }

        echo "\n<script type=\"application/ld+json\">{$json}</script>\n";
    }
}, 99);
