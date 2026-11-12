/*
 * import_csv -- 銀行明細 CSV を読み込んで内容を表示する CLI。
 *
 * 外部から渡された CSV を parse_row() に流し込む「攻撃面」。
 *
 *   ./import_csv sample.csv
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "csvparse.h"

#define LINE_BUFFER_SIZE 8192

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s <csv-file>\n", argv[0]);
        return 2;
    }

    FILE *fh = fopen(argv[1], "r");
    if (fh == NULL) {
        perror("fopen");
        return 2;
    }

    char line[LINE_BUFFER_SIZE];
    int line_number = 0;
    long total = 0;

    while (fgets(line, sizeof(line), fh) != NULL) {
        line[strcspn(line, "\r\n")] = '\0';
        line_number++;

        if (line_number == 1) {
            char header[MAX_FIELD_LEN];
            if (parse_header(line, header, sizeof(header)) == 0) {
                printf("header column: %s\n", header);
            }
            continue;
        }

        if (line[0] == '\0') {
            continue;
        }

        expense_row_t *row = parse_row(line);
        if (row == NULL) {
            fprintf(stderr, "line %d: malformed, skipped\n", line_number);
            continue;
        }

        printf("%-20s %10ld\n", row->name, row->amount_jpy);
        total += row->amount_jpy;
        free_row(row);
    }

    fclose(fh);
    printf("%-20s %10ld\n", "TOTAL", total);
    return 0;
}
