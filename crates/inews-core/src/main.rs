use std::path::PathBuf;

use clap::{Parser, Subcommand};
use inews_core::{normalize_url, validate};

#[derive(Parser)]
#[command(name = "inews-core", version, about = "Schema and URL normalization")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Canonicalize a URL for deduplication.
    Normalize { url: String },
    /// Validate a daily result JSON file.
    Validate { file: PathBuf },
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Command::Normalize { url } => {
            println!("{}", normalize_url(&url));
        }
        Command::Validate { file } => {
            let text = std::fs::read_to_string(&file)?;
            let value: serde_json::Value = serde_json::from_str(&text)?;
            match validate(&value) {
                Ok(()) => println!("OK {}", file.display()),
                Err(errors) => {
                    for error in errors {
                        eprintln!("{error}");
                    }
                    std::process::exit(1);
                }
            }
        }
    }
    Ok(())
}
