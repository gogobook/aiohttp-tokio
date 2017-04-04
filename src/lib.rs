extern crate async_tokio;
#[macro_use] extern crate log;
#[macro_use] extern crate cpython;

use cpython::*;
use async_tokio::new_event_loop;
use async_tokio::spawn_event_loop;
// pub use server::create_server;


py_module_initializer!(_ext, init_aiohttp, PyInit__aiohttp, |py, m| {
    m.add(py, "__doc__", "Aiohttp event loop based on tokio")?;
    m.add(py, "spawn_event_loop", py_fn!(py, spawn_event_loop(name: &PyString)))?;
    m.add(py, "new_event_loop", py_fn!(py, new_event_loop()))?;

    async_tokio::register_classes(py, m)?;
    Ok(())
});
