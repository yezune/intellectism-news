use std::io::Write;

use assert_cmd::Command;

#[test]
fn cli_validate_ok() {
    let mut file = tempfile::NamedTempFile::new().unwrap();
    write!(
        file,
        r#"{{"date":"2026-11-10","field":"labor","generated_at":"2026-11-10T07:17:00+09:00","fetched":1,"errors":{{}},"items":[{{"id":"url:abc","field":"labor","source":"rss:ILO","title":"Layoffs","url":"https://example.com/a","published":"2026-11-09T00:00:00+00:00","summary":"","score":4.5,"tags":[],"primary_source":null,"candidate":true}}],"candidates":["url:abc"]}}"#
    )
    .unwrap();
    Command::cargo_bin("inews-core")
        .unwrap()
        .arg("validate")
        .arg(file.path())
        .assert()
        .success();
}

#[test]
fn cli_validate_rejects() {
    let mut file = tempfile::NamedTempFile::new().unwrap();
    write!(file, r#"{{"date":"x"}}"#).unwrap();
    Command::cargo_bin("inews-core")
        .unwrap()
        .arg("validate")
        .arg(file.path())
        .assert()
        .failure();
}

#[test]
fn cli_normalize() {
    Command::cargo_bin("inews-core")
        .unwrap()
        .arg("normalize")
        .arg("https://Example.COM:443/path/?utm_source=x&b=2&a=1#frag")
        .assert()
        .success()
        .stdout("https://example.com/path?a=1&b=2\n");
}
