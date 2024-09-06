use codspeed_criterion_compat::{criterion_group, criterion_main, Criterion};
use nix::{
    libc::exit,
    unistd::{getegid, geteuid, getgid, getuid},
};
use std::fs::File;
use std::io::{self, Read};

fn read_file(path: &str) -> io::Result<String> {
    let mut file = File::open(path)?;
    let mut content = String::new();
    file.read_to_string(&mut content)?;
    Ok(content)
}

fn test_func() {
    // 获取当前用户和组的 ID
    let uid = getuid();
    let euid = geteuid();
    let gid = getgid();
    let egid = getegid();

    // 打印当前权限信息
    println!("Current UID: {}", uid);
    println!("Effective UID: {}", euid);
    println!("Current GID: {}", gid);
    println!("Effective GID: {}", egid);

    // 检查是否以 root 权限运行
    if uid != 0.into() {
        println!("This program is no root run.");
    } else {
        // 以root权限执行的代码
        println!("Running as root!");
        match read_file("/etc/shadow") {
            Ok(content) => {
                println!("File content:\n{}", content);
            }
            Err(e) => {
                eprintln!("Failed to read the file: {}", e);
            }
        }
    }
    unsafe { exit(0) };
}

pub fn criterion_benchmark(c: &mut Criterion) {
    c.bench_function("test func", |b| {
        b.iter(|| {
            test_func();
        });
    });
}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);
