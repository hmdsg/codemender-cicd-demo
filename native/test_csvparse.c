/*
 * csvparse の正常系テスト。
 *
 * ここにあるのは「修正で壊してはいけない振る舞い」。
 */

#include <stdio.h>
#include <string.h>

#include "csvparse.h"

static int failures = 0;

#define CHECK(cond, msg)                                    \
    do {                                                    \
        if (!(cond)) {                                      \
            printf("  FAIL: %s\n", (msg));                  \
            failures++;                                     \
        } else {                                            \
            printf("  ok:   %s\n", (msg));                  \
        }                                                   \
    } while (0)

static void test_parses_simple_row(void) {
    printf("test_parses_simple_row\n");
    expense_row_t *row = parse_row("taxi,3200");
    CHECK(row != NULL, "row is parsed");
    if (row) {
        CHECK(strcmp(row->name, "taxi") == 0, "name is 'taxi'");
        CHECK(row->amount_jpy == 3200, "amount is 3200");
        free_row(row);
    }
}

static void test_parses_multibyte_name(void) {
    printf("test_parses_multibyte_name\n");
    /* 回帰ガード: 日本語の費目名が壊れないこと。 */
    expense_row_t *row = parse_row("会議費,12800");
    CHECK(row != NULL, "row is parsed");
    if (row) {
        CHECK(strcmp(row->name, "会議費") == 0, "name is '会議費'");
        CHECK(row->amount_jpy == 12800, "amount is 12800");
        free_row(row);
    }
}

static void test_parses_maximum_length_name(void) {
    printf("test_parses_maximum_length_name\n");
    /* 回帰ガード: 境界ちょうど (63 バイト) は切り詰めずに受け付けること。 */
    char line[128];
    memset(line, 'a', 63);
    line[63] = '\0';
    strcat(line, ",500");

    expense_row_t *row = parse_row(line);
    CHECK(row != NULL, "row is parsed");
    if (row) {
        CHECK(strlen(row->name) == 63, "63-byte name is preserved in full");
        CHECK(row->amount_jpy == 500, "amount is 500");
        free_row(row);
    }
}

static void test_row_without_comma_is_rejected(void) {
    printf("test_row_without_comma_is_rejected\n");
    CHECK(parse_row("no-comma-here") == NULL, "malformed row returns NULL");
}

static void test_header_is_truncated_safely(void) {
    printf("test_header_is_truncated_safely\n");
    char out[MAX_FIELD_LEN];
    char line[256];
    memset(line, 'h', 200);
    line[200] = '\0';
    strcat(line, ",amount");

    CHECK(parse_header(line, out, sizeof(out)) == 0, "parse_header succeeds");
    CHECK(strlen(out) == MAX_FIELD_LEN - 1, "long header is truncated to 63 bytes");
}

int main(void) {
    test_parses_simple_row();
    test_parses_multibyte_name();
    test_parses_maximum_length_name();
    test_row_without_comma_is_rejected();
    test_header_is_truncated_safely();

    if (failures == 0) {
        printf("\nAll csvparse tests passed.\n");
        return 0;
    }
    printf("\n%d check(s) failed.\n", failures);
    return 1;
}
