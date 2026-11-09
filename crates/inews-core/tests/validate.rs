use inews_core::{normalize_url, validate};
use serde_json::json;

fn valid() -> serde_json::Value {
    json!({
        "date": "2026-11-10",
        "field": "labor",
        "generated_at": "2026-11-10T07:17:00+09:00",
        "fetched": 1,
        "errors": {},
        "items": [{
            "id": "url:abc",
            "field": "labor",
            "source": "rss:ILO",
            "title": "Layoffs",
            "url": "https://example.com/a",
            "published": "2026-11-09T00:00:00+00:00",
            "summary": "",
            "score": 4.5,
            "tags": [],
            "primary_source": null,
            "candidate": true
        }],
        "candidates": ["url:abc"]
    })
}

#[test]
fn validate_accepts_valid() {
    assert!(validate(&valid()).is_ok());
}

#[test]
fn validate_rejects_missing_items() {
    let mut value = valid();
    value.as_object_mut().unwrap().remove("items");
    assert!(validate(&value).is_err());
}

#[test]
fn validate_rejects_duplicate_ids() {
    let mut value = valid();
    let item = value["items"][0].clone();
    value["items"].as_array_mut().unwrap().push(item);
    assert!(validate(&value).is_err());
}

#[test]
fn validate_rejects_candidate_not_in_items() {
    let mut value = valid();
    value["candidates"] = json!(["missing"]);
    assert!(validate(&value).is_err());
}

#[test]
fn validate_rejects_invalid_url() {
    let mut value = valid();
    value["items"][0]["url"] = json!("not-a-url");
    assert!(validate(&value).is_err());
}

#[test]
fn validate_rejects_bad_date() {
    let mut value = valid();
    value["date"] = json!("2026-13-01");
    assert!(validate(&value).is_err());
}

#[test]
fn validate_rejects_non_numeric_score() {
    let mut value = valid();
    value["items"][0]["score"] = json!("x");
    assert!(validate(&value).is_err());
}

#[test]
fn validate_rejects_candidate_false() {
    let mut value = valid();
    value["items"][0]["candidate"] = json!(false);
    assert!(validate(&value).is_err());
}

#[test]
fn validate_rejects_too_many_candidates() {
    let mut value = valid();
    value["candidates"] = json!([
        "url:abc", "url:abc", "url:abc", "url:abc", "url:abc", "url:abc", "url:abc", "url:abc",
        "url:abc", "url:abc", "url:abc"
    ]);
    assert!(validate(&value).is_err());
}

#[test]
fn normalize_url_removes_tracking_and_fragment() {
    let got = normalize_url("https://Example.COM:443/path/?utm_source=x&b=2&a=1#frag");
    assert_eq!(got, "https://example.com/path?a=1&b=2");
}

#[test]
fn normalize_url_keeps_root() {
    let got = normalize_url("https://example.com/");
    assert_eq!(got, "https://example.com/");
}

#[test]
fn normalize_url_keeps_non_http() {
    let got = normalize_url("mailto:a@b.com");
    assert_eq!(got, "mailto:a@b.com");
}
