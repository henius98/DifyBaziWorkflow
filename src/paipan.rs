use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Serialize, Deserialize)]
pub struct BaziChart {
    pub bz: Value,
    pub ss: Vec<String>,
    pub cg: Vec<Vec<String>>,
    pub cgss: Vec<Vec<String>>,
    pub ny: Vec<String>,
    pub szshensha: Vec<Vec<String>>,
    pub dyshensha: Value,
    pub dayun: Vec<String>,
    pub kongwang: String,
    pub taixi: String,
    pub taiyuan: String,
    pub minggong: String,
    pub shenggong: String,
    pub sex: i32,
    #[serde(default)]
    pub lunar_date: String,
}

pub async fn fetch_bazi_chart(
    client: &Client,
    date: &str, // YYYY-MM-DD
    hour: u32,
    minute: u32,
    gender: u8, // 1 for male, 0 for female
) -> crate::logger::AppResult<(BaziChart, String)> {
    let date_str = format!("{} {:02}:{:02}", date, hour, minute);
    let api_url = format!(
        "https://bzapi4.iwzbz.com/getbasebz8.php?d={}&s={}&today=undefined&vip=0&userguid=&yzs=0",
        date_str, gender
    );

    let response = client.get(&api_url).send().await?.error_for_status()?;
    let raw_data: Value = response.json().await?;

    let mut chart: BaziChart = serde_json::from_value(raw_data.clone())?;
    
    if let Some(lunar) = chart.bz.get("8").and_then(|v| v.as_str()) {
        chart.lunar_date = lunar.to_string();
    }

    Ok((chart, raw_data.to_string()))
}

pub fn format_bazi_for_prompt(chart: &BaziChart) -> String {
    let sex_str = if chart.sex == 1 { "男" } else { "女" };
    
    let y_stem_branch = format!("{}{}", chart.bz.get("0").and_then(|v| v.as_str()).unwrap_or(""), chart.bz.get("1").and_then(|v| v.as_str()).unwrap_or(""));
    let m_stem_branch = format!("{}{}", chart.bz.get("2").and_then(|v| v.as_str()).unwrap_or(""), chart.bz.get("3").and_then(|v| v.as_str()).unwrap_or(""));
    let d_stem_branch = format!("{}{}", chart.bz.get("4").and_then(|v| v.as_str()).unwrap_or(""), chart.bz.get("5").and_then(|v| v.as_str()).unwrap_or(""));
    let h_stem_branch = format!("{}{}", chart.bz.get("6").and_then(|v| v.as_str()).unwrap_or(""), chart.bz.get("7").and_then(|v| v.as_str()).unwrap_or(""));

    let bz_str = format!("{}年 {}月 {}日 {}时", y_stem_branch, m_stem_branch, d_stem_branch, h_stem_branch);
    let ss_str = chart.ss.join(" ");
    let ny_str = chart.ny.join(" ");

    let cg_str = chart.cg.iter().zip(chart.cgss.iter())
        .map(|(c, s)| {
            let pairs: Vec<String> = c.iter().zip(s.iter())
                .map(|(stem, god)| format!("{}({})", stem, god))
                .collect();
            format!("[{}]", pairs.join(" "))
        })
        .collect::<Vec<String>>()
        .join(" ");

    let shensha_str = chart.szshensha.iter()
        .map(|s| s.join(" "))
        .collect::<Vec<String>>()
        .join(" | ");

    let dayun_str = chart.dayun.join(" ");

    format!(
        "性别：{}\n农历：{}\n四柱：{}\n十神：{}\n纳音：{}\n藏干：{}\n空亡：{}\n大运：{}\n四柱神煞：{}\n胎息：{}\n胎元：{}\n命宫：{}\n身宫：{}",
        sex_str,
        chart.lunar_date,
        bz_str,
        ss_str,
        ny_str,
        cg_str,
        chart.kongwang,
        dayun_str,
        shensha_str,
        chart.taixi,
        chart.taiyuan,
        chart.minggong,
        chart.shenggong
    )
}
